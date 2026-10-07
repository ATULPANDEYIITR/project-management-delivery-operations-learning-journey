#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

struct Date {
    int year;
    int month;
    int day;

    bool operator<(const Date& other) const {
        if (year != other.year) return year < other.year;
        if (month != other.month) return month < other.month;
        return day < other.day;
    }

    bool operator==(const Date& other) const {
        return year == other.year &&
               month == other.month &&
               day == other.day;
    }

    bool operator<=(const Date& other) const {
        return *this < other || *this == other;
    }

    bool operator>=(const Date& other) const {
        return other <= *this;
    }

    std::string str() const {
        std::ostringstream output;
        output << year << "-"
               << std::setw(2) << std::setfill('0') << month << "-"
               << std::setw(2) << std::setfill('0') << day;
        return output.str();
    }
};

struct Task {
    std::string id;
    std::string name;
    Date start;
    Date end;
    std::string owner;
    std::vector<std::string> dependencies;
    int duration;
    int progress;
    int priority;
};

struct Milestone {
    std::string name;
    Date due;
    bool completed;
};

class RepositoryTimelineEngine {
private:
    std::map<std::string, Task> tasks;
    std::vector<Milestone> milestones;

    static int dateKey(const Date& date) {
        return date.year * 10000 + date.month * 100 + date.day;
    }

    bool visitForCycle(
        const std::string& taskId,
        std::set<std::string>& visiting,
        std::set<std::string>& visited
    ) const {
        if (visiting.contains(taskId)) {
            return true;
        }

        if (visited.contains(taskId)) {
            return false;
        }

        visiting.insert(taskId);

        const auto& task = tasks.at(taskId);

        for (const auto& dependency : task.dependencies) {
            if (tasks.contains(dependency) &&
                visitForCycle(dependency, visiting, visited)) {
                return true;
            }
        }

        visiting.erase(taskId);
        visited.insert(taskId);
        return false;
    }

public:
    void addTask(const Task& task) {
        if (tasks.contains(task.id)) {
            throw std::invalid_argument("Duplicate task ID: " + task.id);
        }

        if (task.start > task.end) {
            throw std::invalid_argument(
                "Task " + task.id + " has an invalid date range."
            );
        }

        if (task.progress < 0 || task.progress > 100) {
            throw std::invalid_argument(
                "Task progress must be between 0 and 100."
            );
        }

        for (const auto& dependency : task.dependencies) {
            if (dependency == task.id) {
                throw std::invalid_argument(
                    "A task cannot depend on itself."
                );
            }
        }

        tasks.emplace(task.id, task);
    }

    void addMilestone(const Milestone& milestone) {
        milestones.push_back(milestone);
    }

    std::vector<std::string> validateDependencies() const {
        std::vector<std::string> errors;

        for (const auto& [id, task] : tasks) {
            for (const auto& dependencyId : task.dependencies) {
                auto dependency = tasks.find(dependencyId);

                if (dependency == tasks.end()) {
                    errors.push_back(
                        id + " references missing dependency " + dependencyId
                    );
                    continue;
                }

                if (dependency->second.end >= task.start) {
                    errors.push_back(
                        id + " starts before dependency " +
                        dependencyId + " finishes"
                    );
                }
            }
        }

        return errors;
    }

    bool hasCycle() const {
        std::set<std::string> visiting;
        std::set<std::string> visited;

        for (const auto& [id, task] : tasks) {
            if (visitForCycle(id, visiting, visited)) {
                return true;
            }
        }

        return false;
    }

    std::pair<std::vector<std::string>, int> criticalPath() const {
        auto errors = validateDependencies();

        if (!errors.empty()) {
            throw std::runtime_error(
                "Invalid dependencies prevent critical-path analysis."
            );
        }

        if (hasCycle()) {
            throw std::runtime_error(
                "Cyclic dependencies prevent critical-path analysis."
            );
        }

        std::map<std::string, int> longestFinish;
        std::map<std::string, std::string> predecessor;

        for (const auto& [id, task] : tasks) {
            int bestPrevious = 0;
            std::string bestDependency;

            for (const auto& dependency : task.dependencies) {
                int candidate = longestFinish[dependency];

                if (candidate > bestPrevious) {
                    bestPrevious = candidate;
                    bestDependency = dependency;
                }
            }

            longestFinish[id] = bestPrevious + task.duration;
            predecessor[id] = bestDependency;
        }

        std::string finalTask;
        int maximum = 0;

        for (const auto& [id, duration] : longestFinish) {
            if (duration > maximum) {
                maximum = duration;
                finalTask = id;
            }
        }

        std::vector<std::string> path;

        while (!finalTask.empty()) {
            path.push_back(finalTask);
            finalTask = predecessor[finalTask];
        }

        std::reverse(path.begin(), path.end());
        return {path, maximum};
    }

    double weightedProgress() const {
        long long weightedProgress = 0;
        long long totalWeight = 0;

        for (const auto& [id, task] : tasks) {
            totalWeight += task.duration;
            weightedProgress +=
                static_cast<long long>(task.duration) * task.progress;
        }

        if (totalWeight == 0) {
            return 0.0;
        }

        return static_cast<double>(weightedProgress) /
               static_cast<double>(totalWeight);
    }

    void printSchedule() const {
        std::cout << "\nPROJECT GOVERNANCE TIMELINE\n";
        std::cout << std::left
                  << std::setw(8) << "ID"
                  << std::setw(28) << "Task"
                  << std::setw(14) << "Start"
                  << std::setw(14) << "End"
                  << std::setw(12) << "Progress"
                  << "\n";

        std::cout << std::string(76, '-') << "\n";

        for (const auto& [id, task] : tasks) {
            std::cout << std::left
                      << std::setw(8) << task.id
                      << std::setw(28) << task.name
                      << std::setw(14) << task.start.str()
                      << std::setw(14) << task.end.str()
                      << std::setw(12) << (std::to_string(task.progress) + "%")
                      << "\n";
        }
    }

    void printRisks(const Date& asOf) const {
        std::cout << "\nSCHEDULE RISKS AS OF " << asOf.str() << "\n";

        bool found = false;

        for (const auto& [id, task] : tasks) {
            if (task.end < asOf && task.progress < 100) {
                std::cout << "OVERDUE: " << id << " - "
                          << task.name << "\n";
                found = true;
            }

            if (task.start <= asOf &&
                asOf <= task.end &&
                task.progress == 0) {
                std::cout << "NOT STARTED: " << id << " - "
                          << task.name << "\n";
                found = true;
            }

            if (task.priority >= 2 && task.progress < 50) {
                std::cout << "HIGH PRIORITY: " << id << " - "
                          << task.name << "\n";
                found = true;
            }
        }

        if (!found) {
            std::cout << "No schedule risks detected.\n";
        }
    }
};

Task makeTask(
    std::string id,
    std::string name,
    Date start,
    Date end,
    std::string owner,
    std::vector<std::string> dependencies,
    int duration,
    int progress,
    int priority
) {
    return {
        std::move(id),
        std::move(name),
        start,
        end,
        std::move(owner),
        std::move(dependencies),
        duration,
        progress,
        priority
    };
}

int main() {
    try {
        RepositoryTimelineEngine engine;

        engine.addTask(makeTask(
            "T01",
            "Requirements baseline",
            {2026, 10, 12},
            {2026, 10, 16},
            "Business Analyst",
            {},
            5,
            100,
            2
        ));

        engine.addTask(makeTask(
            "T02",
            "Architecture approval",
            {2026, 10, 19},
            {2026, 10, 23},
            "Solution Architect",
            {"T01"},
            5,
            80,
            2
        ));

        engine.addTask(makeTask(
            "T03",
            "Core implementation",
            {2026, 10, 26},
            {2026, 11, 6},
            "Engineering Team",
            {"T02"},
            12,
            40,
            3
        ));

        engine.addTask(makeTask(
            "T04",
            "Integration testing",
            {2026, 11, 9},
            {2026, 11, 13},
            "QA Team",
            {"T03"},
            5,
            0,
            2
        ));

        engine.addTask(makeTask(
            "T05",
            "Production release",
            {2026, 11, 16},
            {2026, 11, 17},
            "Release Manager",
            {"T04"},
            2,
            0,
            3
        ));

        engine.addMilestone({
            "Requirements complete",
            {2026, 10, 16},
            true
        });

        engine.addMilestone({
            "Production release",
            {2026, 11, 17},
            false
        });

        engine.printSchedule();

        std::cout << "\nDEPENDENCY VALIDATION\n";
        auto dependencyErrors = engine.validateDependencies();

        if (dependencyErrors.empty()) {
            std::cout << "All dependency relationships are valid.\n";
        } else {
            for (const auto& error : dependencyErrors) {
                std::cout << "ERROR: " << error << "\n";
            }
        }

        std::cout << "\nCRITICAL PATH ANALYSIS\n";
        auto [path, duration] = engine.criticalPath();

        for (std::size_t i = 0; i < path.size(); ++i) {
            if (i != 0) {
                std::cout << " -> ";
            }
            std::cout << path[i];
        }

        std::cout << "\nCritical-path duration: "
                  << duration << " task-days\n";

        std::cout << "\nWEIGHTED PROGRESS\n";
        std::cout << std::fixed << std::setprecision(1)
                  << engine.weightedProgress() << "%\n";

        engine.printRisks({2026, 11, 10});

        std::cout << "\nCASE STUDY DECISION\n";
        std::cout
            << "The release task is governed by the testing dependency, so "
               "an incomplete testing task directly delays the release window.\n";

        RepositoryTimelineEngine invalidEngine;

        invalidEngine.addTask(makeTask(
            "A",
            "First task",
            {2026, 12, 1},
            {2026, 12, 5},
            "Team A",
            {"B"},
            5,
            0,
            1
        ));

        invalidEngine.addTask(makeTask(
            "B",
            "Second task",
            {2026, 12, 8},
            {2026, 12, 10},
            "Team B",
            {"A"},
            3,
            0,
            1
        ));

        std::cout << "\nCYCLE TEST\n";
        std::cout << "Cycle detected: "
                  << std::boolalpha
                  << invalidEngine.hasCycle()
                  << "\n";

    } catch (const std::exception& exception) {
        std::cerr << "Timeline engine error: "
                  << exception.what()
                  << "\n";
        return 1;
    }

    return 0;
}
