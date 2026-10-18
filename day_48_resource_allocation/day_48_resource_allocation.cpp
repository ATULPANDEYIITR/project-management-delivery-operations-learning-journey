#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

using namespace std;

/*
 * Case study: allocating engineering workloads across a mixed compute fleet.
 *
 * The scheduler uses:
 * - Type and tag compatibility to identify eligible resources.
 * - Priority and deadlines to order tasks.
 * - Dependency finish times to enforce execution precedence.
 * - Earliest-feasible-start scheduling to avoid reservation conflicts.
 * - Copy-then-commit planning to prevent partial state changes.
 *
 * This is a deterministic heuristic, not a globally optimal scheduler.
 */

struct Resource {
    string id;
    string type;
    double capacity;
    double hourlyCost;
    set<string> tags;
};

struct Task {
    string id;
    string name;
    string type;
    double demand;
    double duration;
    int priority;
    vector<string> dependencies;
    set<string> requiredTags;
    double deadline;
};

struct Allocation {
    string taskId;
    string resourceId;
    double demand;
    double start;
    double end;
};

struct Plan {
    vector<Allocation> allocations;
    map<string, string> rejected;
};

class ResourceAllocationEngine {
private:
    map<string, Resource> resources;
    map<string, Task> tasks;
    map<string, vector<Allocation>> reservations;

    static constexpr double EPSILON = 1e-9;

    bool compatible(const Task& task, const Resource& resource) const {
        if (task.type != resource.type ||
            task.demand > resource.capacity + EPSILON) {
            return false;
        }

        for (const auto& tag : task.requiredTags) {
            if (resource.tags.find(tag) == resource.tags.end()) {
                return false;
            }
        }
        return true;
    }

    void validateInputs() const {
        for (const auto& [id, task] : tasks) {
            if (id.empty() || task.demand <= 0 ||
                task.duration <= 0 || task.priority < 0) {
                throw invalid_argument("Invalid task definition: " + id);
            }

            for (const auto& dependency : task.dependencies) {
                if (tasks.find(dependency) == tasks.end()) {
                    throw invalid_argument(
                        "Unknown dependency " + dependency +
                        " for task " + id
                    );
                }
            }
        }

        set<string> visiting;
        set<string> visited;

        function<void(const string&)> visit = [&](const string& id) {
            if (visiting.count(id)) {
                throw invalid_argument("Dependency cycle detected.");
            }
            if (visited.count(id)) return;

            visiting.insert(id);
            for (const auto& dependency : tasks.at(id).dependencies) {
                visit(dependency);
            }
            visiting.erase(id);
            visited.insert(id);
        };

        for (const auto& [id, task] : tasks) {
            visit(id);
        }
    }

    double earliestStart(
        const string& resourceId,
        double requestedStart,
        double duration,
        const map<string, vector<Allocation>>& schedule
    ) const {
        auto existing = schedule.at(resourceId);
        sort(existing.begin(), existing.end(),
             [](const Allocation& a, const Allocation& b) {
                 return a.start < b.start;
             });

        double candidate = requestedStart;
        for (const auto& allocation : existing) {
            if (candidate + duration <= allocation.start + EPSILON) {
                break;
            }
            if (candidate < allocation.end - EPSILON) {
                candidate = allocation.end;
            }
        }
        return candidate;
    }

public:
    ResourceAllocationEngine(
        vector<Resource> resourceList,
        vector<Task> taskList
    ) {
        for (const auto& resource : resourceList) {
            if (resource.id.empty() || resource.capacity <= 0 ||
                resource.hourlyCost < 0) {
                throw invalid_argument("Invalid resource definition.");
            }
            if (!resources.emplace(resource.id, resource).second) {
                throw invalid_argument("Duplicate resource ID.");
            }
            reservations[resource.id] = {};
        }

        for (const auto& task : taskList) {
            if (!tasks.emplace(task.id, task).second) {
                throw invalid_argument("Duplicate task ID.");
            }
        }

        validateInputs();
    }

    Plan buildPlan() {
        // Keep proposed reservations local until the entire plan is complete.
        auto proposedReservations = reservations;
        Plan plan;
        set<string> pending;

        for (const auto& [id, task] : tasks) {
            pending.insert(id);
        }

        map<string, double> finishTimes;

        while (!pending.empty()) {
            vector<Task> ready;

            for (const auto& id : pending) {
                const auto& task = tasks.at(id);
                bool resolved = true;

                for (const auto& dependency : task.dependencies) {
                    if (!finishTimes.count(dependency) &&
                        !plan.rejected.count(dependency)) {
                        resolved = false;
                        break;
                    }
                }

                if (resolved) ready.push_back(task);
            }

            if (ready.empty()) {
                for (const auto& id : pending) {
                    plan.rejected[id] = "Dependency resolution failed.";
                }
                break;
            }

            sort(ready.begin(), ready.end(),
                 [](const Task& a, const Task& b) {
                     if (a.priority != b.priority) {
                         return a.priority > b.priority;
                     }
                     if (a.deadline != b.deadline) {
                         return a.deadline < b.deadline;
                     }
                     return a.id < b.id;
                 });

            Task task = ready.front();
            pending.erase(task.id);

            bool failedDependency = false;
            for (const auto& dependency : task.dependencies) {
                if (plan.rejected.count(dependency)) {
                    plan.rejected[task.id] =
                        "Dependency " + dependency + " was rejected.";
                    failedDependency = true;
                    break;
                }
            }
            if (failedDependency) continue;

            double dependencyFinish = 0.0;
            for (const auto& dependency : task.dependencies) {
                dependencyFinish = max(
                    dependencyFinish, finishTimes.at(dependency)
                );
            }

            vector<tuple<double, double, string>> candidates;

            for (const auto& [resourceId, resource] : resources) {
                if (!compatible(task, resource)) continue;

                double start = earliestStart(
                    resourceId,
                    dependencyFinish,
                    task.duration,
                    proposedReservations
                );
                double end = start + task.duration;

                if (end <= task.deadline + EPSILON) {
                    candidates.emplace_back(
                        start, resource.hourlyCost, resourceId
                    );
                }
            }

            if (candidates.empty()) {
                plan.rejected[task.id] =
                    "No compatible resource can meet the deadline.";
                continue;
            }

            sort(candidates.begin(), candidates.end());
            const auto& [start, cost, resourceId] = candidates.front();
            Allocation allocation{
                task.id,
                resourceId,
                task.demand,
                start,
                start + task.duration
            };

            proposedReservations[resourceId].push_back(allocation);
            plan.allocations.push_back(allocation);
            finishTimes[task.id] = allocation.end;
        }

        // Commit is a single state replacement after successful planning.
        reservations = move(proposedReservations);
        return plan;
    }

    vector<string> validate(const Plan& plan) const {
        vector<string> errors;
        map<string, vector<Allocation>> byResource;
        map<string, Allocation> byTask;

        for (const auto& allocation : plan.allocations) {
            if (!resources.count(allocation.resourceId) ||
                !tasks.count(allocation.taskId)) {
                errors.push_back("Unknown task or resource in allocation.");
                continue;
            }

            const auto& resource = resources.at(allocation.resourceId);
            const auto& task = tasks.at(allocation.taskId);

            if (!compatible(task, resource)) {
                errors.push_back("Incompatible assignment: " + task.id);
            }
            if (fabs(allocation.demand - task.demand) > EPSILON) {
                errors.push_back("Incorrect allocated demand: " + task.id);
            }
            if (allocation.end <= allocation.start) {
                errors.push_back("Invalid interval: " + task.id);
            }
            if (!byTask.emplace(task.id, allocation).second) {
                errors.push_back("Task allocated more than once: " + task.id);
            }
            byResource[resource.id].push_back(allocation);
        }

        for (auto& [resourceId, allocations] : byResource) {
            sort(allocations.begin(), allocations.end(),
                 [](const Allocation& a, const Allocation& b) {
                     return a.start < b.start;
                 });

            for (size_t i = 1; i < allocations.size(); ++i) {
                if (allocations[i].start <
                    allocations[i - 1].end - EPSILON) {
                    errors.push_back(
                        "Overlapping reservations on " + resourceId
                    );
                }
            }
        }

        for (const auto& [taskId, allocation] : byTask) {
            for (const auto& dependency : tasks.at(taskId).dependencies) {
                if (!byTask.count(dependency)) {
                    errors.push_back(
                        "Missing dependency " + dependency +
                        " for " + taskId
                    );
                } else if (allocation.start <
                           byTask.at(dependency).end - EPSILON) {
                    errors.push_back(
                        "Dependency timing violation for " + taskId
                    );
                }
            }
        }

        return errors;
    }

    double totalCost(const Plan& plan) const {
        double total = 0;
        for (const auto& allocation : plan.allocations) {
            total += (allocation.end - allocation.start) *
                     resources.at(allocation.resourceId).hourlyCost;
        }
        return total;
    }

    void print(const Plan& plan) const {
        cout << fixed << setprecision(1);
        cout << "\nENGINEERING WORKLOAD ALLOCATION\n";
        cout << left << setw(12) << "Task"
             << setw(12) << "Resource"
             << right << setw(10) << "Start"
             << setw(10) << "Finish"
             << setw(10) << "Demand" << '\n';

        for (const auto& allocation : plan.allocations) {
            cout << left << setw(12) << allocation.taskId
                 << setw(12) << allocation.resourceId
                 << right << setw(10) << allocation.start
                 << setw(10) << allocation.end
                 << setw(10) << allocation.demand << '\n';
        }

        cout << "\nRejected tasks:\n";
        for (const auto& [id, reason] : plan.rejected) {
            cout << "  " << id << ": " << reason << '\n';
        }

        cout << "\nEstimated resource cost: " << totalCost(plan) << '\n';

        const auto errors = validate(plan);
        if (errors.empty()) {
            cout << "Validation: PASSED\n";
        } else {
            cout << "Validation: FAILED\n";
            for (const auto& error : errors) {
                cout << "  " << error << '\n';
            }
        }
    }
};

int main() {
    try {
        vector<Resource> resources{
            {"GPU-A", "compute", 16, 18.0, {"cuda", "linux"}},
            {"CPU-A", "compute", 8, 6.0, {"linux"}},
            {"DB-A", "database", 12, 14.0, {"postgresql", "backup"}},
            {"OPS-A", "operations", 4, 10.0, {"production"}}
        };

        vector<Task> tasks{
            {"ETL", "Prepare data", "compute", 6, 2, 8,
             {}, {"linux"}, 10},
            {"TRAIN", "Train forecasting model", "compute", 14, 4, 10,
             {"ETL"}, {"cuda"}, 9},
            {"MIGRATE", "Migrate database", "database", 8, 3, 7,
             {}, {"postgresql", "backup"}, 8},
            {"VERIFY", "Verify model output", "compute", 4, 2, 6,
             {"TRAIN"}, {"linux"}, 12},
            {"DEPLOY", "Deploy service", "operations", 3, 2, 10,
             {"MIGRATE", "VERIFY"}, {"production"}, 16},
            {"HPC", "Oversized simulation", "compute", 32, 5, 3,
             {}, {"linux"}, 100}
        };

        ResourceAllocationEngine engine(resources, tasks);
        Plan plan = engine.buildPlan();
        engine.print(plan);

        if (!engine.validate(plan).empty()) {
            return 1;
        }
    } catch (const exception& error) {
        cerr << "Allocation engine error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
