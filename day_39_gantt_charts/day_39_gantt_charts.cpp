#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <map>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

struct Date {
    int year;
    int month;
    int day;

    bool operator<(const Date& other) const {
        return tie(year, month, day) < tie(other.year, other.month, other.day);
    }

    bool operator<=(const Date& other) const {
        return !(other < *this);
    }

    bool operator==(const Date& other) const {
        return tie(year, month, day) == tie(other.year, other.month, other.day);
    }
};

static Date parseDate(const string& value) {
    Date result{};
    char firstDash;
    char secondDash;

    stringstream stream(value);
    stream >> result.year >> firstDash >> result.month
           >> secondDash >> result.day;

    if (!stream || firstDash != '-' || secondDash != '-') {
        throw invalid_argument("Invalid date: " + value);
    }

    return result;
}

static long long serialDay(const Date& date) {
    int y = date.year;
    unsigned m = date.month;
    unsigned d = date.day;

    y -= m <= 2;
    const int era = (y >= 0 ? y : y - 399) / 400;
    const unsigned yearOfEra = static_cast<unsigned>(y - era * 400);
    const unsigned dayOfYear =
        (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1;
    const unsigned dayOfEra =
        yearOfEra * 365 + yearOfEra / 4 -
        yearOfEra / 100 + dayOfYear;

    return era * 146097LL +
           static_cast<long long>(dayOfEra) - 719468LL;
}

static int durationDays(const Date& start, const Date& end) {
    if (end < start) {
        throw invalid_argument("End date precedes start date.");
    }

    return static_cast<int>(serialDay(end) - serialDay(start) + 1);
}

struct Task {
    string id;
    string name;
    Date start;
    Date end;
    vector<string> dependencies;
    string resource;
    int progress = 0;
    bool milestone = false;

    int duration() const {
        return durationDays(start, end);
    }
};

class ScheduleEngine {
private:
    map<string, Task> tasks;

public:
    void addTask(const Task& task) {
        if (tasks.contains(task.id)) {
            throw invalid_argument("Duplicate task: " + task.id);
        }

        if (task.progress < 0 || task.progress > 100) {
            throw invalid_argument("Invalid progress for " + task.id);
        }

        if (task.milestone && !(task.start == task.end)) {
            throw invalid_argument("Milestone must occupy one date.");
        }

        tasks.emplace(task.id, task);
    }

    const Task& getTask(const string& id) const {
        auto iterator = tasks.find(id);

        if (iterator == tasks.end()) {
            throw invalid_argument("Unknown task: " + id);
        }

        return iterator->second;
    }

    vector<string> topologicalOrder() const {
        map<string, int> indegree;
        map<string, vector<string>> successors;

        for (const auto& [id, task] : tasks) {
            indegree[id] = 0;
            successors[id] = {};
        }

        for (const auto& [id, task] : tasks) {
            for (const string& dependency : task.dependencies) {
                getTask(dependency);

                ++indegree[id];
                successors[dependency].push_back(id);
            }
        }

        queue<string> ready;

        for (const auto& [id, degree] : indegree) {
            if (degree == 0) {
                ready.push(id);
            }
        }

        vector<string> ordered;

        while (!ready.empty()) {
            string current = ready.front();
            ready.pop();

            ordered.push_back(current);

            for (const string& successor : successors[current]) {
                --indegree[successor];

                if (indegree[successor] == 0) {
                    ready.push(successor);
                }
            }
        }

        if (ordered.size() != tasks.size()) {
            throw runtime_error("Circular dependency detected.");
        }

        return ordered;
    }

    void validateDependencies() const {
        topologicalOrder();

        for (const auto& [id, task] : tasks) {
            for (const string& dependency : task.dependencies) {
                const Task& predecessor = getTask(dependency);

                if (!(predecessor.end < task.start)) {
                    throw runtime_error(
                        "Dependency violation: " +
                        predecessor.id + " must finish before " +
                        task.id + " starts."
                    );
                }
            }
        }
    }

    vector<string> criticalPath() const {
        vector<string> ordered = topologicalOrder();

        map<string, int> earliestFinish;
        map<string, string> previous;

        for (const string& id : ordered) {
            const Task& task = getTask(id);

            if (task.dependencies.empty()) {
                earliestFinish[id] = task.duration();
                previous[id] = "";
                continue;
            }

            string bestDependency = task.dependencies.front();

            for (const string& dependency : task.dependencies) {
                if (earliestFinish[dependency] >
                    earliestFinish[bestDependency]) {
                    bestDependency = dependency;
                }
            }

            earliestFinish[id] =
                earliestFinish[bestDependency] + task.duration();

            previous[id] = bestDependency;
        }

        string finalTask = ordered.front();

        for (const string& id : ordered) {
            if (earliestFinish[id] > earliestFinish[finalTask]) {
                finalTask = id;
            }
        }

        vector<string> path;

        while (!finalTask.empty()) {
            path.push_back(finalTask);
            finalTask = previous[finalTask];
        }

        reverse(path.begin(), path.end());
        return path;
    }

    map<string, vector<pair<string, string>>> resourceConflicts() const {
        map<string, vector<string>> resources;

        for (const auto& [id, task] : tasks) {
            if (!task.resource.empty()) {
                resources[task.resource].push_back(id);
            }
        }

        map<string, vector<pair<string, string>>> conflicts;

        for (auto& [resource, ids] : resources) {
            sort(ids.begin(), ids.end(),
                 [&](const string& left, const string& right) {
                     return getTask(left).start < getTask(right).start;
                 });

            for (size_t i = 0; i < ids.size(); ++i) {
                for (size_t j = i + 1; j < ids.size(); ++j) {
                    const Task& first = getTask(ids[i]);
                    const Task& second = getTask(ids[j]);

                    if (first.end < second.start) {
                        break;
                    }

                    if (second.start <= first.end) {
                        conflicts[resource].push_back(
                            {first.id, second.id}
                        );
                    }
                }
            }
        }

        return conflicts;
    }

    void render() const {
        if (tasks.empty()) {
            cout << "No tasks.\n";
            return;
        }

        Date projectStart = tasks.begin()->second.start;

        for (const auto& [id, task] : tasks) {
            if (task.start < projectStart) {
                projectStart = task.start;
            }
        }

        cout << "\nGANTT CHART: Supply Chain Analytics Deployment\n\n";

        for (const auto& [id, task] : tasks) {
            int offset = durationDays(projectStart, task.start) - 1;
            string prefix(offset, ' ');

            string bar;

            if (task.milestone) {
                bar = "*";
            } else {
                int completed =
                    task.duration() * task.progress / 100;

                bar.append(completed, '|');
                bar.append(task.duration() - completed, '.');
            }

            cout << left << setw(28) << task.name
                 << " " << prefix << bar
                 << "  " << task.progress << "%\n";
        }

        cout << "\nLegend: | completed, . remaining, * milestone\n";
    }

    void printScheduleMetrics() const {
        int plannedDays = 0;
        double completedEquivalent = 0.0;

        for (const auto& [id, task] : tasks) {
            plannedDays += task.duration();
            completedEquivalent +=
                task.duration() * task.progress / 100.0;
        }

        double completion =
            plannedDays == 0
                ? 0.0
                : completedEquivalent / plannedDays * 100.0;

        cout << fixed << setprecision(2);
        cout << "\nSchedule metrics\n";
        cout << "Planned task-days: " << plannedDays << '\n';
        cout << "Completed equivalent task-days: "
             << completedEquivalent << '\n';
        cout << "Weighted completion: " << completion << "%\n";
    }
};

int main() {
    try {
        ScheduleEngine schedule;

        schedule.addTask({
            "REQ",
            "Business Requirements",
            parseDate("2026-10-12"),
            parseDate("2026-10-16"),
            {},
            "Business",
            100,
            false
        });

        schedule.addTask({
            "DATA",
            "Data Pipeline",
            parseDate("2026-10-19"),
            parseDate("2026-10-30"),
            {"REQ"},
            "Data Engineering",
            60,
            false
        });

        schedule.addTask({
            "MODEL",
            "Forecasting Model",
            parseDate("2026-10-26"),
            parseDate("2026-11-06"),
            {"REQ"},
            "Data Science",
            45,
            false
        });

        schedule.addTask({
            "UI",
            "Operations Dashboard",
            parseDate("2026-10-26"),
            parseDate("2026-11-13"),
            {"REQ"},
            "Frontend",
            35,
            false
        });

        schedule.addTask({
            "TEST",
            "Acceptance Testing",
            parseDate("2026-11-16"),
            parseDate("2026-11-20"),
            {"DATA", "MODEL", "UI"},
            "QA",
            0,
            false
        });

        schedule.addTask({
            "LIVE",
            "Production Launch",
            parseDate("2026-11-23"),
            parseDate("2026-11-23"),
            {"TEST"},
            "Release",
            0,
            true
        });

        schedule.validateDependencies();
        schedule.render();
        schedule.printScheduleMetrics();

        cout << "\nCritical path\n";
        for (size_t i = 0; i < schedule.criticalPath().size(); ++i) {
            if (i > 0) {
                cout << " -> ";
            }
            cout << schedule.criticalPath()[i];
        }
        cout << '\n';

        cout << "\nResource conflicts\n";
        auto conflicts = schedule.resourceConflicts();

        if (conflicts.empty()) {
            cout << "No overlapping resource assignments detected.\n";
        } else {
            for (const auto& [resource, pairs] : conflicts) {
                cout << resource << ":\n";
                for (const auto& [first, second] : pairs) {
                    cout << "  " << first << " overlaps " << second << '\n';
                }
            }
        }

        cout << "\nCase study completed successfully.\n";
    }
    catch (const exception& error) {
        cerr << "Schedule error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
