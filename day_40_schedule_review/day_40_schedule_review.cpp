#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;

struct Date {
    int year{};
    int month{};
    int day{};

    bool operator<(const Date& other) const {
        if (year != other.year) return year < other.year;
        if (month != other.month) return month < other.month;
        return day < other.day;
    }

    bool operator<=(const Date& other) const {
        return !(other < *this);
    }

    bool operator>(const Date& other) const {
        return other < *this;
    }

    bool operator>=(const Date& other) const {
        return !(*this < other);
    }

    bool operator==(const Date& other) const {
        return year == other.year && month == other.month && day == other.day;
    }
};

Date parseDate(const string& value) {
    if (value.size() != 10 || value[4] != '-' || value[7] != '-') {
        throw invalid_argument("Date must use YYYY-MM-DD.");
    }

    Date result{
        stoi(value.substr(0, 4)),
        stoi(value.substr(5, 2)),
        stoi(value.substr(8, 2))
    };

    if (result.month < 1 || result.month > 12 ||
        result.day < 1 || result.day > 31) {
        throw invalid_argument("Invalid calendar date: " + value);
    }

    return result;
}

string dateString(const Date& date) {
    ostringstream output;
    output << setfill('0')
           << setw(4) << date.year << "-"
           << setw(2) << date.month << "-"
           << setw(2) << date.day;
    return output.str();
}

int serialDay(const Date& date) {
    // Howard Hinnant's civil-date arithmetic gives stable day differences
    // without relying on platform-specific time-zone behavior.
    int y = date.year - (date.month <= 2);
    const int era = (y >= 0 ? y : y - 399) / 400;
    const unsigned yearOfEra = static_cast<unsigned>(y - era * 400);
    const unsigned adjustedMonth =
        static_cast<unsigned>(date.month + (date.month > 2 ? -3 : 9));
    const unsigned dayOfYear =
        (153 * adjustedMonth + 2) / 5 + static_cast<unsigned>(date.day) - 1;
    const unsigned dayOfEra =
        yearOfEra * 365 + yearOfEra / 4 - yearOfEra / 100 + dayOfYear;

    return era * 146097 + static_cast<int>(dayOfEra);
}

int inclusiveDuration(const Date& start, const Date& end) {
    return serialDay(end) - serialDay(start) + 1;
}

enum class Status {
    Planned,
    InProgress,
    Complete,
    Blocked
};

string statusString(Status status) {
    switch (status) {
        case Status::Planned: return "planned";
        case Status::InProgress: return "in_progress";
        case Status::Complete: return "complete";
        case Status::Blocked: return "blocked";
    }
    return "unknown";
}

struct Task {
    string id;
    string name;
    Date start;
    Date end;
    string owner;
    vector<string> dependencies;
    double plannedHours{};
    double progress{};
    Status status{Status::Planned};

    int duration() const {
        return inclusiveDuration(start, end);
    }

    bool overlaps(const Task& other) const {
        return start <= other.end && other.start <= end;
    }
};

struct Conflict {
    string owner;
    string firstTask;
    string secondTask;
    Date start;
    Date end;
};

struct ReviewEvidence {
    vector<string> dependencyIssues;
    vector<Conflict> resourceConflicts;
    map<string, double> capacityExcess;
    vector<string> cycle;
};

class RepositoryGovernanceSchedule {
private:
    map<string, Task> tasks;

    bool cycleDfs(
        const string& id,
        set<string>& visiting,
        set<string>& visited,
        vector<string>& path
    ) const {
        if (visiting.count(id)) {
            path.push_back(id);
            return true;
        }

        if (visited.count(id)) {
            return false;
        }

        visiting.insert(id);
        path.push_back(id);

        const auto& task = tasks.at(id);

        for (const string& dependency : task.dependencies) {
            if (!tasks.count(dependency)) {
                continue;
            }

            if (cycleDfs(dependency, visiting, visited, path)) {
                return true;
            }
        }

        path.pop_back();
        visiting.erase(id);
        visited.insert(id);
        return false;
    }

    pair<int, vector<string>> longestPathFrom(
        const string& id,
        unordered_map<string, pair<int, vector<string>>>& memo
    ) const {
        if (memo.count(id)) {
            return memo.at(id);
        }

        const Task& task = tasks.at(id);

        if (task.dependencies.empty()) {
            return memo[id] = {task.duration(), {id}};
        }

        int bestDuration = 0;
        vector<string> bestPath;

        for (const string& dependency : task.dependencies) {
            if (!tasks.count(dependency)) {
                continue;
            }

            auto candidate = longestPathFrom(dependency, memo);

            if (candidate.first > bestDuration) {
                bestDuration = candidate.first;
                bestPath = candidate.second;
            }
        }

        bestPath.push_back(id);

        return memo[id] = {
            bestDuration + task.duration(),
            bestPath
        };
    }

public:
    void addTask(const Task& task) {
        if (tasks.count(task.id)) {
            throw invalid_argument("Duplicate task ID: " + task.id);
        }

        if (task.end < task.start) {
            throw invalid_argument(
                "Task " + task.id + " has an end date before its start date."
            );
        }

        if (task.progress < 0 || task.progress > 100) {
            throw invalid_argument(
                "Task " + task.id + " has invalid progress."
            );
        }

        tasks.emplace(task.id, task);
    }

    const map<string, Task>& allTasks() const {
        return tasks;
    }

    vector<string> validateDependencies() const {
        vector<string> issues;

        for (const auto& [id, task] : tasks) {
            for (const string& dependencyId : task.dependencies) {
                auto dependency = tasks.find(dependencyId);

                if (dependency == tasks.end()) {
                    issues.push_back(
                        id + ": missing dependency " + dependencyId
                    );
                    continue;
                }

                if (dependency->second.end > task.start) {
                    issues.push_back(
                        id + ": dependency " + dependencyId +
                        " finishes " + dateString(dependency->second.end) +
                        " after task starts " + dateString(task.start)
                    );
                }
            }
        }

        return issues;
    }

    vector<string> detectCycle() const {
        set<string> visiting;
        set<string> visited;
        vector<string> path;

        for (const auto& [id, task] : tasks) {
            if (cycleDfs(id, visiting, visited, path)) {
                return path;
            }
        }

        return {};
    }

    vector<Conflict> detectResourceConflicts() const {
        map<string, vector<const Task*>> byOwner;

        for (const auto& [id, task] : tasks) {
            byOwner[task.owner].push_back(&task);
        }

        vector<Conflict> conflicts;

        for (auto& [owner, ownerTasks] : byOwner) {
            sort(
                ownerTasks.begin(),
                ownerTasks.end(),
                [](const Task* a, const Task* b) {
                    return a->start < b->start;
                }
            );

            for (size_t i = 0; i < ownerTasks.size(); ++i) {
                for (size_t j = i + 1; j < ownerTasks.size(); ++j) {
                    if (ownerTasks[j]->start > ownerTasks[i]->end) {
                        break;
                    }

                    if (ownerTasks[i]->overlaps(*ownerTasks[j])) {
                        conflicts.push_back({
                            owner,
                            ownerTasks[i]->id,
                            ownerTasks[j]->id,
                            max(ownerTasks[i]->start, ownerTasks[j]->start),
                            min(ownerTasks[i]->end, ownerTasks[j]->end)
                        });
                    }
                }
            }
        }

        return conflicts;
    }

    map<string, double> capacityExcess(
        const map<string, double>& capacity
    ) const {
        map<string, double> workload;

        for (const auto& [id, task] : tasks) {
            workload[task.owner] += task.plannedHours;
        }

        map<string, double> excess;

        for (const auto& [owner, hours] : workload) {
            auto limit = capacity.find(owner);

            if (limit != capacity.end() && hours > limit->second) {
                excess[owner] = hours - limit->second;
            }
        }

        return excess;
    }

    pair<int, vector<string>> criticalPath() const {
        if (!detectCycle().empty()) {
            throw logic_error(
                "Critical path cannot be calculated for a cyclic dependency graph."
            );
        }

        unordered_map<string, pair<int, vector<string>>> memo;
        pair<int, vector<string>> best{0, {}};

        for (const auto& [id, task] : tasks) {
            auto candidate = longestPathFrom(id, memo);

            if (candidate.first > best.first) {
                best = candidate;
            }
        }

        return best;
    }

    ReviewEvidence collectEvidence(
        const map<string, double>& capacity
    ) const {
        ReviewEvidence evidence;
        evidence.dependencyIssues = validateDependencies();
        evidence.resourceConflicts = detectResourceConflicts();
        evidence.capacityExcess = capacityExcess(capacity);
        evidence.cycle = detectCycle();
        return evidence;
    }
};

class MergePlanningDecision {
public:
    static string evaluate(const ReviewEvidence& evidence) {
        if (!evidence.cycle.empty()) {
            return "ESCALATE";
        }

        if (!evidence.dependencyIssues.empty() ||
            !evidence.resourceConflicts.empty() ||
            !evidence.capacityExcess.empty()) {
            return "REVISE";
        }

        return "ACCEPT";
    }
};

Task makeTask(
    string id,
    string name,
    string start,
    string end,
    string owner,
    vector<string> dependencies,
    double hours,
    double progress,
    Status status
) {
    return Task{
        move(id),
        move(name),
        parseDate(start),
        parseDate(end),
        move(owner),
        move(dependencies),
        hours,
        progress,
        status
    };
}

void printEvidence(
    const ReviewEvidence& evidence,
    const string& decision
) {
    cout << "\nSchedule Review Decision: " << decision << "\n";

    cout << "\nDependency findings:\n";
    if (evidence.dependencyIssues.empty()) {
        cout << "  none\n";
    } else {
        for (const string& issue : evidence.dependencyIssues) {
            cout << "  " << issue << "\n";
        }
    }

    cout << "\nResource conflicts:\n";
    if (evidence.resourceConflicts.empty()) {
        cout << "  none\n";
    } else {
        for (const Conflict& conflict : evidence.resourceConflicts) {
            cout << "  " << conflict.owner << ": "
                 << conflict.firstTask << " overlaps "
                 << conflict.secondTask << " from "
                 << dateString(conflict.start) << " to "
                 << dateString(conflict.end) << "\n";
        }
    }

    cout << "\nCapacity findings:\n";
    if (evidence.capacityExcess.empty()) {
        cout << "  none\n";
    } else {
        for (const auto& [owner, excess] : evidence.capacityExcess) {
            cout << "  " << owner << " exceeds capacity by "
                 << fixed << setprecision(1) << excess << " hours\n";
        }
    }

    if (!evidence.cycle.empty()) {
        cout << "\nDependency cycle: ";
        for (size_t i = 0; i < evidence.cycle.size(); ++i) {
            if (i > 0) cout << " -> ";
            cout << evidence.cycle[i];
        }
        cout << "\n";
    }
}

int main() {
    try {
        RepositoryGovernanceSchedule schedule;

        schedule.addTask(makeTask(
            "PLAN",
            "Planning baseline",
            "2026-10-01",
            "2026-10-03",
            "Asha",
            {},
            18,
            100,
            Status::Complete
        ));

        schedule.addTask(makeTask(
            "DESIGN",
            "System design",
            "2026-10-04",
            "2026-10-06",
            "Ravi",
            {"PLAN"},
            20,
            100,
            Status::Complete
        ));

        schedule.addTask(makeTask(
            "BUILD",
            "Implementation",
            "2026-10-07",
            "2026-10-12",
            "Ravi",
            {"DESIGN"},
            36,
            55,
            Status::InProgress
        ));

        schedule.addTask(makeTask(
            "DATA",
            "Schedule data validation",
            "2026-10-08",
            "2026-10-11",
            "Meera",
            {"DESIGN"},
            24,
            70,
            Status::InProgress
        ));

        schedule.addTask(makeTask(
            "TEST",
            "Integrated verification",
            "2026-10-13",
            "2026-10-16",
            "Asha",
            {"BUILD", "DATA"},
            28,
            0,
            Status::Planned
        ));

        schedule.addTask(makeTask(
            "RELEASE",
            "Operational release",
            "2026-10-19",
            "2026-10-19",
            "Asha",
            {"TEST"},
            8,
            0,
            Status::Planned
        ));

        map<string, double> capacity{
            {"Asha", 70.0},
            {"Ravi", 65.0},
            {"Meera", 40.0}
        };

        ReviewEvidence evidence = schedule.collectEvidence(capacity);
        string decision = MergePlanningDecision::evaluate(evidence);

        cout << "SCHEDULE REVIEW CASE STUDY\n";
        cout << "==========================\n";

        auto critical = schedule.criticalPath();

        cout << "\nCritical path: ";
        for (size_t i = 0; i < critical.second.size(); ++i) {
            if (i > 0) cout << " -> ";
            cout << critical.second[i];
        }

        cout << "\nCritical-path duration: "
             << critical.first << " calendar days\n";

        printEvidence(evidence, decision);

        cout << "\nTask duration profile:\n";
        for (const auto& [id, task] : schedule.allTasks()) {
            cout << "  " << id
                 << " | owner=" << task.owner
                 << " | duration=" << task.duration()
                 << " days | status=" << statusString(task.status)
                 << " | progress=" << task.progress << "%\n";
        }

        cout << "\nThe review separates schedule facts from policy evaluation.\n";
        cout << "A dependency error is structural, a resource conflict is "
                "capacity-related, and the final decision is a governance "
                "judgment over those findings.\n";

    } catch (const exception& error) {
        cerr << "Schedule review failed: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
