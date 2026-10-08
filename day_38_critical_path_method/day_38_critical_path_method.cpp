#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <queue>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

/*
 * Critical Path Method: Repository Infrastructure Delivery Case Study
 *
 * This C++17 program models a technical infrastructure project where
 * activities represent engineering work required before a production
 * environment can be delivered.
 *
 * The program demonstrates:
 *   - activity-on-node dependency modeling
 *   - topological sorting
 *   - cycle detection
 *   - forward pass
 *   - backward pass
 *   - total float
 *   - critical activity identification
 *   - critical path reconstruction
 *   - delay sensitivity
 *
 * The implementation deliberately uses C++ containers and explicit
 * graph algorithms because the dependency network is the central
 * computational object in Critical Path Method analysis.
 */

struct Activity {
    std::string id;
    std::string name;
    double duration;
    std::vector<std::string> predecessors;
};

struct ScheduleEntry {
    Activity activity;
    double earliestStart = 0.0;
    double earliestFinish = 0.0;
    double latestStart = 0.0;
    double latestFinish = 0.0;
    double totalFloat = 0.0;
};

class CriticalPathEngine {
private:
    static constexpr double EPSILON = 1e-9;

    std::unordered_map<std::string, Activity> activities;
    std::unordered_map<std::string, std::vector<std::string>> successors;
    std::vector<std::string> order;
    std::unordered_map<std::string, ScheduleEntry> schedule;

    void validateActivities() const {
        for (const auto& [id, activity] : activities) {
            if (id.empty()) {
                throw std::invalid_argument(
                    "Activity ID cannot be empty."
                );
            }

            if (activity.name.empty()) {
                throw std::invalid_argument(
                    "Activity name cannot be empty."
                );
            }

            if (!std::isfinite(activity.duration) ||
                activity.duration < 0.0) {
                throw std::invalid_argument(
                    "Activity duration must be finite and non-negative: " +
                    id
                );
            }

            std::unordered_set<std::string> seen;

            for (const auto& predecessor : activity.predecessors) {
                if (!activities.contains(predecessor)) {
                    throw std::invalid_argument(
                        "Unknown predecessor " + predecessor +
                        " referenced by " + id
                    );
                }

                if (!seen.insert(predecessor).second) {
                    throw std::invalid_argument(
                        "Duplicate predecessor " + predecessor +
                        " in activity " + id
                    );
                }
            }
        }
    }

    void buildGraph() {
        for (const auto& [id, activity] : activities) {
            successors[id];
        }

        for (const auto& [id, activity] : activities) {
            for (const auto& predecessor : activity.predecessors) {
                successors[predecessor].push_back(id);
            }
        }
    }

    void topologicalSort() {
        std::unordered_map<std::string, int> indegree;

        for (const auto& [id, activity] : activities) {
            indegree[id] =
                static_cast<int>(activity.predecessors.size());
        }

        std::queue<std::string> ready;

        for (const auto& [id, degree] : indegree) {
            if (degree == 0) {
                ready.push(id);
            }
        }

        while (!ready.empty()) {
            std::string current = ready.front();
            ready.pop();

            order.push_back(current);

            for (const auto& successor : successors[current]) {
                --indegree[successor];

                if (indegree[successor] == 0) {
                    ready.push(successor);
                }
            }
        }

        if (order.size() != activities.size()) {
            throw std::invalid_argument(
                "Dependency graph contains a cycle."
            );
        }
    }

public:
    explicit CriticalPathEngine(
        const std::vector<Activity>& inputActivities
    ) {
        for (const auto& activity : inputActivities) {
            if (activities.contains(activity.id)) {
                throw std::invalid_argument(
                    "Duplicate activity ID: " + activity.id
                );
            }

            activities.emplace(activity.id, activity);
        }

        validateActivities();
        buildGraph();
        topologicalSort();
    }

    void calculate() {
        schedule.clear();

        /*
         * Forward pass:
         *
         * An activity cannot begin until all predecessors have finished.
         * Therefore ES is the largest predecessor EF.
         */
        for (const auto& id : order) {
            const auto& activity = activities.at(id);

            double earliestStart = 0.0;

            for (const auto& predecessor : activity.predecessors) {
                earliestStart = std::max(
                    earliestStart,
                    schedule.at(predecessor).earliestFinish
                );
            }

            ScheduleEntry entry;
            entry.activity = activity;
            entry.earliestStart = earliestStart;
            entry.earliestFinish =
                earliestStart + activity.duration;

            schedule[id] = entry;
        }

        const double projectDuration = getProjectDuration();

        /*
         * Backward pass:
         *
         * A terminal activity can finish as late as the project completion
         * time. A non-terminal activity must finish before the earliest
         * latest-start value of all successors.
         */
        for (auto iterator = order.rbegin();
             iterator != order.rend();
             ++iterator) {

            const std::string& id = *iterator;
            auto& entry = schedule.at(id);

            double latestFinish = projectDuration;

            if (!successors[id].empty()) {
                latestFinish =
                    std::numeric_limits<double>::infinity();

                for (const auto& successor : successors[id]) {
                    latestFinish = std::min(
                        latestFinish,
                        schedule.at(successor).latestStart
                    );
                }
            }

            entry.latestFinish = latestFinish;
            entry.latestStart =
                latestFinish - entry.activity.duration;

            entry.totalFloat = std::max(
                0.0,
                entry.latestStart - entry.earliestStart
            );
        }
    }

    double getProjectDuration() const {
        double result = 0.0;

        for (const auto& [id, entry] : schedule) {
            result = std::max(
                result,
                entry.earliestFinish
            );
        }

        return result;
    }

    bool isCritical(const std::string& id) const {
        return std::abs(
            schedule.at(id).totalFloat
        ) <= EPSILON;
    }

    std::vector<std::string> criticalActivities() const {
        std::vector<std::string> result;

        for (const auto& id : order) {
            if (isCritical(id)) {
                result.push_back(id);
            }
        }

        return result;
    }

    std::vector<std::vector<std::string>> criticalPaths() const {
        std::unordered_set<std::string> critical;

        for (const auto& id : order) {
            if (isCritical(id)) {
                critical.insert(id);
            }
        }

        std::vector<std::string> starts;

        for (const auto& id : order) {
            if (!critical.contains(id)) {
                continue;
            }

            bool hasCriticalPredecessor = false;

            for (const auto& predecessor :
                 activities.at(id).predecessors) {
                if (critical.contains(predecessor)) {
                    hasCriticalPredecessor = true;
                    break;
                }
            }

            if (!hasCriticalPredecessor) {
                starts.push_back(id);
            }
        }

        std::vector<std::vector<std::string>> paths;

        std::function<void(
            const std::vector<std::string>&
        )> visit;

        visit = [&](const std::vector<std::string>& path) {
            const std::string& current = path.back();
            std::vector<std::string> next;

            for (const auto& successor : successors.at(current)) {
                if (!critical.contains(successor)) {
                    continue;
                }

                const double gap =
                    schedule.at(successor).earliestStart -
                    schedule.at(current).earliestFinish;

                if (std::abs(gap) <= EPSILON) {
                    next.push_back(successor);
                }
            }

            if (next.empty()) {
                paths.push_back(path);
                return;
            }

            for (const auto& successor : next) {
                auto extended = path;
                extended.push_back(successor);
                visit(extended);
            }
        };

        for (const auto& start : starts) {
            visit({start});
        }

        return paths;
    }

    double simulateDelay(
        const std::string& activityId,
        double delay
    ) const {
        if (!activities.contains(activityId)) {
            throw std::invalid_argument(
                "Unknown activity: " + activityId
            );
        }

        if (!std::isfinite(delay) || delay < 0.0) {
            throw std::invalid_argument(
                "Delay must be finite and non-negative."
            );
        }

        std::vector<Activity> modified;

        for (const auto& [id, activity] : activities) {
            Activity copy = activity;

            if (id == activityId) {
                copy.duration += delay;
            }

            modified.push_back(copy);
        }

        CriticalPathEngine simulation(modified);
        simulation.calculate();

        return simulation.getProjectDuration();
    }

    void printSchedule() const {
        std::cout << "\nCRITICAL PATH SCHEDULE\n";
        std::cout << std::string(110, '=') << '\n';

        std::cout
            << std::left
            << std::setw(8) << "ID"
            << std::setw(34) << "Activity"
            << std::right
            << std::setw(8) << "Dur"
            << std::setw(8) << "ES"
            << std::setw(8) << "EF"
            << std::setw(8) << "LS"
            << std::setw(8) << "LF"
            << std::setw(10) << "Float"
            << std::setw(14) << "Status"
            << '\n';

        std::cout << std::string(110, '-') << '\n';

        for (const auto& id : order) {
            const auto& entry = schedule.at(id);

            std::cout
                << std::left
                << std::setw(8) << id
                << std::setw(34)
                << entry.activity.name.substr(0, 33)
                << std::right
                << std::fixed
                << std::setprecision(1)
                << std::setw(8) << entry.activity.duration
                << std::setw(8) << entry.earliestStart
                << std::setw(8) << entry.earliestFinish
                << std::setw(8) << entry.latestStart
                << std::setw(8) << entry.latestFinish
                << std::setw(10) << entry.totalFloat
                << std::setw(14)
                << (isCritical(id)
                        ? "CRITICAL"
                        : "NON-CRITICAL")
                << '\n';
        }

        std::cout << std::string(110, '-') << '\n';
        std::cout
            << "Project duration: "
            << getProjectDuration()
            << '\n';

        std::cout << "\nCritical path(s):\n";

        for (const auto& path : criticalPaths()) {
            for (std::size_t i = 0; i < path.size(); ++i) {
                if (i > 0) {
                    std::cout << " -> ";
                }

                std::cout << path[i];
            }

            std::cout << '\n';
        }
    }

    const std::vector<std::string>& getOrder() const {
        return order;
    }

    const ScheduleEntry& getEntry(
        const std::string& id
    ) const {
        return schedule.at(id);
    }
};

std::vector<Activity> createInfrastructureProject() {
    /*
     * Technical scenario:
     *
     * A platform team is preparing a production service. Infrastructure
     * provisioning and application deployment can proceed in parallel,
     * but integration cannot begin until both are complete.
     *
     * Security validation and performance testing then converge into the
     * production release activity.
     */
    return {
        {"A", "Requirements baseline", 3.0, {}},
        {"B", "Architecture approval", 4.0, {"A"}},
        {"C", "Network provisioning", 5.0, {"B"}},
        {"D", "Database provisioning", 4.0, {"B"}},
        {"E", "Application deployment", 7.0, {"B"}},
        {"F", "Platform integration", 3.0, {"C", "D", "E"}},
        {"G", "Performance testing", 4.0, {"F"}},
        {"H", "Security validation", 5.0, {"F"}},
        {"I", "Operations readiness", 2.0, {"B"}},
        {"J", "Production cutover", 2.0, {"G", "H", "I"}}
    };
}

void demonstrateDelaySensitivity(
    const CriticalPathEngine& project
) {
    std::cout << "\nDELAY SENSITIVITY\n";
    std::cout << std::string(70, '=') << '\n';

    const double baseline =
        project.getProjectDuration();

    for (const auto& id : project.getOrder()) {
        const auto& entry =
            project.getEntry(id);

        const double delayedDuration =
            project.simulateDelay(id, 1.0);

        const double impact =
            delayedDuration - baseline;

        std::cout
            << std::left
            << std::setw(8) << id
            << std::setw(32)
            << entry.activity.name
            << "float=" << std::setw(6)
            << entry.totalFloat
            << " project impact=" << impact
            << '\n';
    }
}

void demonstrateMultipleCriticalPaths() {
    std::cout << "\nMULTIPLE CRITICAL PATH CASE\n";
    std::cout << std::string(70, '=') << '\n';

    CriticalPathEngine project({
        {"S", "Project start", 1.0, {}},
        {"A", "Engineering branch", 5.0, {"S"}},
        {"B", "Operations branch", 5.0, {"S"}},
        {"E", "Project completion", 1.0, {"A", "B"}}
    });

    project.calculate();
    project.printSchedule();
}

void demonstrateValidation() {
    std::cout << "\nVALIDATION FAILURES\n";
    std::cout << std::string(70, '=') << '\n';

    try {
        CriticalPathEngine invalid({
            {"A", "Requirements", 2.0, {}},
            {"B", "Implementation", 3.0, {"MISSING"}}
        });

        invalid.calculate();
    }
    catch (const std::exception& error) {
        std::cout
            << "Unknown dependency rejected: "
            << error.what()
            << '\n';
    }

    try {
        CriticalPathEngine cyclic({
            {"A", "First", 2.0, {"B"}},
            {"B", "Second", 3.0, {"A"}}
        });

        cyclic.calculate();
    }
    catch (const std::exception& error) {
        std::cout
            << "Circular dependency rejected: "
            << error.what()
            << '\n';
    }
}

int main() {
    try {
        std::cout
            << "CRITICAL PATH METHOD\n"
            << "Infrastructure Delivery Case Study\n";

        CriticalPathEngine project(
            createInfrastructureProject()
        );

        project.calculate();
        project.printSchedule();

        demonstrateDelaySensitivity(project);
        demonstrateMultipleCriticalPaths();
        demonstrateValidation();

        std::cout << "\nINTERPRETATION\n";
        std::cout << std::string(70, '=') << '\n';
        std::cout
            << "The critical path is the sequence of dependency-linked "
            << "activities with zero total float that controls the current "
            << "project completion date.\n";

        std::cout
            << "The forward pass answers when work can happen at the "
            << "earliest. The backward pass answers how late that work "
            << "can occur without extending the project.\n";

        std::cout
            << "A one-unit delay to a non-critical activity may have zero "
            << "project impact when the activity has at least one unit of "
            << "available float.\n";

        std::cout
            << "Criticality is not permanent. Duration changes, dependency "
            << "changes, and progress updates can change the controlling "
            << "path and therefore require schedule recalculation.\n";
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal scheduling error: "
            << error.what()
            << '\n';

        return 1;
    }

    return 0;
}
