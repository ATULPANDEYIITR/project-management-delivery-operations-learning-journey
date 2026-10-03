/*
    Activity Sequencing: Determining Activity Order

    C++17 case study:
    A release-engineering team is preparing a software platform release.
    The governance engine receives activities and predecessor relationships,
    validates the dependency graph, creates a dependency-safe order, groups
    activities by execution level, calculates CPM values, identifies critical
    activities, and evaluates whether a requested schedule is logically valid.

    Compile:
        g++ -std=c++17 -Wall -Wextra -pedantic activity_sequencing.cpp -o activity_sequencing

    The implementation intentionally separates:
      - dependency modeling
      - graph validation
      - sequencing
      - schedule analysis
      - business-rule validation
*/

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

struct Activity {
    std::string id;
    std::string name;
    double duration;
    std::set<std::string> predecessors;
};

struct ScheduleEntry {
    double earliestStart = 0.0;
    double earliestFinish = 0.0;
    double latestStart = 0.0;
    double latestFinish = 0.0;
    double totalFloat = 0.0;
};

class ReleaseSequencingEngine {
private:
    std::unordered_map<std::string, Activity> activities_;

    static constexpr double EPSILON = 1e-9;

    std::unordered_map<std::string, std::set<std::string>>
    buildSuccessors() const {
        std::unordered_map<std::string, std::set<std::string>> successors;

        for (const auto& [id, activity] : activities_) {
            (void)activity;
            successors[id];
        }

        for (const auto& [id, activity] : activities_) {
            for (const auto& predecessor : activity.predecessors) {
                if (!activities_.count(predecessor)) {
                    throw std::runtime_error(
                        "Activity " + id +
                        " references unknown predecessor " + predecessor
                    );
                }

                successors[predecessor].insert(id);
            }
        }

        return successors;
    }

public:
    void addActivity(
        const std::string& id,
        const std::string& name,
        double duration,
        const std::set<std::string>& predecessors = {}
    ) {
        if (id.empty()) {
            throw std::invalid_argument("Activity ID cannot be empty.");
        }

        if (name.empty()) {
            throw std::invalid_argument(
                "Activity " + id + " must have a name."
            );
        }

        if (!std::isfinite(duration) || duration < 0.0) {
            throw std::invalid_argument(
                "Activity " + id +
                " must have a finite non-negative duration."
            );
        }

        if (predecessors.count(id)) {
            throw std::invalid_argument(
                "Activity " + id + " cannot depend on itself."
            );
        }

        if (activities_.count(id)) {
            throw std::invalid_argument(
                "Duplicate activity ID: " + id
            );
        }

        activities_.emplace(
            id,
            Activity{id, name, duration, predecessors}
        );
    }

    std::vector<std::string> topologicalOrder() const {
        const auto successors = buildSuccessors();

        std::unordered_map<std::string, int> indegree;

        for (const auto& [id, activity] : activities_) {
            indegree[id] = static_cast<int>(activity.predecessors.size());
        }

        // A priority queue gives deterministic alphabetical selection whenever
        // several activities are dependency-ready at the same time.
        std::priority_queue<
            std::string,
            std::vector<std::string>,
            std::greater<std::string>
        > ready;

        for (const auto& [id, degree] : indegree) {
            if (degree == 0) {
                ready.push(id);
            }
        }

        std::vector<std::string> order;

        while (!ready.empty()) {
            const std::string current = ready.top();
            ready.pop();

            order.push_back(current);

            const auto successorIt = successors.find(current);

            if (successorIt == successors.end()) {
                continue;
            }

            for (const auto& successor : successorIt->second) {
                --indegree[successor];

                if (indegree[successor] == 0) {
                    ready.push(successor);
                }
            }
        }

        if (order.size() != activities_.size()) {
            std::vector<std::string> unresolved;

            for (const auto& [id, degree] : indegree) {
                if (degree > 0) {
                    unresolved.push_back(id);
                }
            }

            std::sort(unresolved.begin(), unresolved.end());

            std::ostringstream message;
            message << "Circular dependency detected. Unresolved activities: ";

            for (std::size_t i = 0; i < unresolved.size(); ++i) {
                if (i > 0) {
                    message << ", ";
                }
                message << unresolved[i];
            }

            throw std::runtime_error(message.str());
        }

        return order;
    }

    std::map<int, std::vector<std::string>> dependencyLevels() const {
        const auto order = topologicalOrder();

        std::unordered_map<std::string, int> levels;
        std::map<int, std::vector<std::string>> result;

        for (const auto& id : order) {
            const auto& activity = activities_.at(id);

            int level = 0;

            for (const auto& predecessor : activity.predecessors) {
                level = std::max(level, levels.at(predecessor) + 1);
            }

            levels[id] = level;
            result[level].push_back(id);
        }

        return result;
    }

    std::unordered_map<std::string, ScheduleEntry> cpmAnalysis(
        double& projectDuration
    ) const {
        const auto order = topologicalOrder();
        const auto successors = buildSuccessors();

        std::unordered_map<std::string, ScheduleEntry> schedule;

        // Forward pass.
        for (const auto& id : order) {
            const auto& activity = activities_.at(id);

            double earliestStart = 0.0;

            for (const auto& predecessor : activity.predecessors) {
                earliestStart = std::max(
                    earliestStart,
                    schedule.at(predecessor).earliestFinish
                );
            }

            ScheduleEntry entry;
            entry.earliestStart = earliestStart;
            entry.earliestFinish = earliestStart + activity.duration;

            schedule[id] = entry;
        }

        projectDuration = 0.0;

        for (const auto& [id, entry] : schedule) {
            (void)id;
            projectDuration = std::max(
                projectDuration,
                entry.earliestFinish
            );
        }

        // Backward pass.
        for (auto it = order.rbegin(); it != order.rend(); ++it) {
            const std::string& id = *it;
            auto& entry = schedule.at(id);

            const auto& children = successors.at(id);

            if (children.empty()) {
                entry.latestFinish = projectDuration;
            } else {
                entry.latestFinish =
                    std::numeric_limits<double>::infinity();

                for (const auto& child : children) {
                    entry.latestFinish = std::min(
                        entry.latestFinish,
                        schedule.at(child).latestStart
                    );
                }
            }

            entry.latestStart =
                entry.latestFinish - activities_.at(id).duration;

            entry.totalFloat =
                entry.latestStart - entry.earliestStart;

            if (std::abs(entry.totalFloat) < EPSILON) {
                entry.totalFloat = 0.0;
            }
        }

        return schedule;
    }

    std::vector<std::string> criticalActivities() const {
        double duration = 0.0;
        const auto schedule = cpmAnalysis(duration);

        std::vector<std::string> critical;

        for (const auto& [id, entry] : schedule) {
            if (std::abs(entry.totalFloat) < EPSILON) {
                critical.push_back(id);
            }
        }

        std::sort(critical.begin(), critical.end());
        return critical;
    }

    bool validateRequestedOrder(
        const std::vector<std::string>& proposedOrder,
        std::string& reason
    ) const {
        if (proposedOrder.size() != activities_.size()) {
            reason =
                "The proposed sequence does not contain exactly one position "
                "for every activity.";
            return false;
        }

        std::unordered_map<std::string, std::size_t> position;

        for (std::size_t index = 0; index < proposedOrder.size(); ++index) {
            const auto& id = proposedOrder[index];

            if (!activities_.count(id)) {
                reason = "Unknown activity in proposed sequence: " + id;
                return false;
            }

            if (position.count(id)) {
                reason = "Activity appears more than once: " + id;
                return false;
            }

            position[id] = index;
        }

        for (const auto& [id, activity] : activities_) {
            for (const auto& predecessor : activity.predecessors) {
                if (position.at(predecessor) >= position.at(id)) {
                    reason =
                        "Invalid dependency order: " + predecessor +
                        " must occur before " + id + ".";
                    return false;
                }
            }
        }

        reason = "The proposed order satisfies every predecessor constraint.";
        return true;
    }

    void printActivities() const {
        std::cout << "\nRelease Activity Network\n";
        std::cout << std::string(90, '-') << '\n';

        std::cout
            << std::left
            << std::setw(8) << "ID"
            << std::setw(34) << "Activity"
            << std::setw(12) << "Duration"
            << "Predecessors\n";

        std::cout << std::string(90, '-') << '\n';

        for (const auto& id : topologicalOrder()) {
            const auto& activity = activities_.at(id);

            std::ostringstream predecessors;

            if (activity.predecessors.empty()) {
                predecessors << "None";
            } else {
                bool first = true;
                for (const auto& predecessor : activity.predecessors) {
                    if (!first) {
                        predecessors << ", ";
                    }
                    predecessors << predecessor;
                    first = false;
                }
            }

            std::cout
                << std::left
                << std::setw(8) << id
                << std::setw(34) << activity.name
                << std::setw(12) << activity.duration
                << predecessors.str()
                << '\n';
        }
    }

    void printCPM() const {
        double projectDuration = 0.0;
        const auto schedule = cpmAnalysis(projectDuration);

        std::cout << "\nCritical Path Method Analysis\n";
        std::cout << std::string(76, '-') << '\n';

        std::cout
            << std::left
            << std::setw(8) << "ID"
            << std::right
            << std::setw(8) << "ES"
            << std::setw(8) << "EF"
            << std::setw(8) << "LS"
            << std::setw(8) << "LF"
            << std::setw(10) << "Float"
            << '\n';

        std::cout << std::string(76, '-') << '\n';

        for (const auto& id : topologicalOrder()) {
            const auto& entry = schedule.at(id);

            std::cout
                << std::left
                << std::setw(8) << id
                << std::right
                << std::fixed
                << std::setprecision(1)
                << std::setw(8) << entry.earliestStart
                << std::setw(8) << entry.earliestFinish
                << std::setw(8) << entry.latestStart
                << std::setw(8) << entry.latestFinish
                << std::setw(10) << entry.totalFloat
                << '\n';
        }

        std::cout << "\nProject duration: "
                  << projectDuration
                  << " working days\n";

        std::cout << "Zero-float activities: ";

        const auto critical = criticalActivities();

        for (std::size_t i = 0; i < critical.size(); ++i) {
            if (i > 0) {
                std::cout << " -> ";
            }
            std::cout << critical[i];
        }

        std::cout << '\n';
    }

    void printDependencyLevels() const {
        const auto levels = dependencyLevels();

        std::cout << "\nDependency Levels\n";
        std::cout << std::string(60, '-') << '\n';

        for (const auto& [level, activities] : levels) {
            std::cout << "Level " << level << ": ";

            for (std::size_t i = 0; i < activities.size(); ++i) {
                if (i > 0) {
                    std::cout << ", ";
                }

                std::cout << activities[i];
            }

            std::cout << '\n';
        }
    }
};

void demonstrateInvalidOrder(
    const ReleaseSequencingEngine& engine
) {
    std::cout << "\nProposed Schedule Validation\n";
    std::cout << std::string(76, '-') << '\n';

    // E is intentionally placed before B, even though E depends on B.
    const std::vector<std::string> invalidOrder = {
        "A", "E", "B", "C", "D", "F", "G", "H", "I"
    };

    std::string reason;

    if (engine.validateRequestedOrder(invalidOrder, reason)) {
        std::cout << "Accepted: " << reason << '\n';
    } else {
        std::cout << "Rejected: " << reason << '\n';
    }
}

void demonstrateValidOrder(
    const ReleaseSequencingEngine& engine
) {
    std::cout << "\nDependency-Safe Proposed Schedule\n";
    std::cout << std::string(76, '-') << '\n';

    const std::vector<std::string> validOrder = {
        "A", "B", "C", "D", "E", "F", "G", "H", "I"
    };

    std::string reason;

    if (engine.validateRequestedOrder(validOrder, reason)) {
        std::cout << "Accepted: " << reason << '\n';

        std::cout << "Order: ";

        for (std::size_t i = 0; i < validOrder.size(); ++i) {
            if (i > 0) {
                std::cout << " -> ";
            }

            std::cout << validOrder[i];
        }

        std::cout << '\n';
    } else {
        std::cout << "Rejected: " << reason << '\n';
    }
}

void demonstrateCycleFailure() {
    std::cout << "\nCycle Detection Case\n";
    std::cout << std::string(76, '-') << '\n';

    ReleaseSequencingEngine cyclic;

    cyclic.addActivity("A", "Requirements", 2, {"C"});
    cyclic.addActivity("B", "Architecture", 3, {"A"});
    cyclic.addActivity("C", "Review", 1, {"B"});

    try {
        (void)cyclic.topologicalOrder();
        std::cout << "Unexpected result: cyclic network was accepted.\n";
    } catch (const std::exception& error) {
        std::cout << "Correctly rejected: "
                  << error.what()
                  << '\n';
    }
}

void demonstrateResourceConstraint() {
    std::cout << "\nLogical Parallelism and Resource Constraints\n";
    std::cout << std::string(76, '-') << '\n';

    std::cout
        << "Activities B and C can both follow A from a dependency perspective.\n"
        << "If both require the same senior architect, dependency analysis alone\n"
        << "does not authorize simultaneous execution. Resource-constrained\n"
        << "scheduling must add a policy that serializes or reallocates work.\n";
}

int main() {
    try {
        ReleaseSequencingEngine engine;

        // Software release case study:
        // Each predecessor represents a real readiness condition for the next
        // activity. B and C can proceed after A and therefore form parallel
        // branches. G waits for all integration inputs.
        engine.addActivity(
            "A",
            "Finalize release scope",
            2
        );

        engine.addActivity(
            "B",
            "Design application architecture",
            3,
            {"A"}
        );

        engine.addActivity(
            "C",
            "Design test strategy",
            2,
            {"A"}
        );

        engine.addActivity(
            "D",
            "Implement persistence layer",
            4,
            {"B"}
        );

        engine.addActivity(
            "E",
            "Implement service layer",
            5,
            {"B"}
        );

        engine.addActivity(
            "F",
            "Prepare integration environment",
            2,
            {"C"}
        );

        engine.addActivity(
            "G",
            "Execute integration testing",
            3,
            {"D", "E", "F"}
        );

        engine.addActivity(
            "H",
            "Perform release validation",
            2,
            {"G"}
        );

        engine.addActivity(
            "I",
            "Deploy production release",
            1,
            {"H"}
        );

        engine.printActivities();
        engine.printDependencyLevels();

        std::cout << "\nTopological Activity Sequence\n";
        std::cout << std::string(76, '-') << '\n';

        const auto order = engine.topologicalOrder();

        for (std::size_t i = 0; i < order.size(); ++i) {
            if (i > 0) {
                std::cout << " -> ";
            }

            std::cout << order[i];
        }

        std::cout << '\n';

        engine.printCPM();

        demonstrateValidOrder(engine);
        demonstrateInvalidOrder(engine);
        demonstrateResourceConstraint();
        demonstrateCycleFailure();

        std::cout << "\nCase Study Interpretation\n";
        std::cout << std::string(76, '-') << '\n';
        std::cout
            << "The dependency graph determines legal activity order without\n"
            << "requiring activities to be performed strictly one at a time.\n"
            << "B and C can become ready after A, while G must wait until D, E,\n"
            << "and F have completed. CPM then distinguishes activities whose\n"
            << "available scheduling slack is zero from activities that can move\n"
            << "within their float without changing the calculated completion date.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Scheduling engine failure: "
                  << error.what()
                  << '\n';

        return 1;
    }
}
