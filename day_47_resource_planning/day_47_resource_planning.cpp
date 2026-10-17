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

enum class ResourceType {
    Person,
    Equipment,
    Budget
};

enum class ReviewState {
    NotReviewed,
    Approved,
    Rejected
};

struct Resource {
    string id;
    string name;
    ResourceType type;
    double weeklyCapacity;
    double hourlyCost;
    set<string> skills;
};

struct Task {
    string id;
    string name;
    double estimatedHours;
    int priority;
    set<string> requiredSkills;
};

struct Allocation {
    string resourceId;
    string taskId;
    double hours;
};

struct CapacityResult {
    bool valid;
    string reason;
};

class ResourceGovernanceEngine {
private:
    map<string, Resource> resources;
    map<string, Task> tasks;
    vector<Allocation> allocations;

    double allocatedHours(const string& resourceId) const {
        double total = 0.0;

        for (const auto& allocation : allocations) {
            if (allocation.resourceId == resourceId) {
                total += allocation.hours;
            }
        }

        return total;
    }

    bool hasRequiredSkills(
        const Resource& resource,
        const Task& task
    ) const {
        for (const auto& skill : task.requiredSkills) {
            if (!resource.skills.contains(skill)) {
                return false;
            }
        }

        return true;
    }

public:
    void addResource(const Resource& resource) {
        if (resources.contains(resource.id)) {
            throw runtime_error(
                "Duplicate resource: " + resource.id
            );
        }

        if (resource.weeklyCapacity <= 0) {
            throw runtime_error(
                "Resource capacity must be positive."
            );
        }

        resources.emplace(resource.id, resource);
    }

    void addTask(const Task& task) {
        if (tasks.contains(task.id)) {
            throw runtime_error(
                "Duplicate task: " + task.id
            );
        }

        if (task.estimatedHours <= 0) {
            throw runtime_error(
                "Task effort must be positive."
            );
        }

        tasks.emplace(task.id, task);
    }

    CapacityResult validateAllocation(
        const string& resourceId,
        const string& taskId,
        double hours
    ) const {
        auto resourceIt = resources.find(resourceId);
        auto taskIt = tasks.find(taskId);

        if (resourceIt == resources.end()) {
            return {false, "Resource does not exist."};
        }

        if (taskIt == tasks.end()) {
            return {false, "Task does not exist."};
        }

        if (hours <= 0) {
            return {false, "Allocation must be positive."};
        }

        const Resource& resource = resourceIt->second;
        const Task& task = taskIt->second;

        if (resource.type != ResourceType::Person) {
            return {false, "This scenario requires a person resource."};
        }

        if (!hasRequiredSkills(resource, task)) {
            return {
                false,
                "Resource does not possess all required skills."
            };
        }

        if (hours > task.estimatedHours) {
            return {
                false,
                "Allocation exceeds task effort."
            };
        }

        const double current = allocatedHours(resourceId);

        if (current + hours > resource.weeklyCapacity) {
            return {
                false,
                "Allocation exceeds available weekly capacity."
            };
        }

        return {true, "Allocation is valid."};
    }

    void allocate(
        const string& resourceId,
        const string& taskId,
        double hours
    ) {
        CapacityResult result =
            validateAllocation(resourceId, taskId, hours);

        if (!result.valid) {
            throw runtime_error(result.reason);
        }

        allocations.push_back({
            resourceId,
            taskId,
            hours
        });
    }

    vector<Resource> findQualifiedResources(
        const string& taskId
    ) const {
        auto taskIt = tasks.find(taskId);

        if (taskIt == tasks.end()) {
            throw runtime_error("Unknown task.");
        }

        vector<Resource> result;

        for (const auto& [id, resource] : resources) {
            if (
                resource.type == ResourceType::Person &&
                hasRequiredSkills(resource, taskIt->second)
            ) {
                result.push_back(resource);
            }
        }

        sort(
            result.begin(),
            result.end(),
            [this](const Resource& left, const Resource& right) {
                const double leftRemaining =
                    left.weeklyCapacity - allocatedHours(left.id);

                const double rightRemaining =
                    right.weeklyCapacity - allocatedHours(right.id);

                return leftRemaining > rightRemaining;
            }
        );

        return result;
    }

    double totalCost() const {
        double total = 0.0;

        for (const auto& allocation : allocations) {
            const auto resourceIt =
                resources.find(allocation.resourceId);

            total +=
                allocation.hours *
                resourceIt->second.hourlyCost;
        }

        return total;
    }

    void printCapacityReport() const {
        cout << "\nCapacity report\n";
        cout << "------------------------------\n";

        for (const auto& [id, resource] : resources) {
            const double used = allocatedHours(id);
            const double percentage =
                used / resource.weeklyCapacity * 100.0;

            cout << left
                 << setw(12) << id
                 << setw(22) << resource.name
                 << right
                 << setw(8) << fixed
                 << setprecision(1) << used
                 << " / "
                 << setw(6) << resource.weeklyCapacity
                 << " h   "
                 << setw(6) << percentage
                 << "%\n";
        }
    }

    void printAllocationRegister() const {
        cout << "\nAllocation register\n";
        cout << "------------------------------\n";

        for (const auto& allocation : allocations) {
            cout << allocation.resourceId
                 << " -> "
                 << allocation.taskId
                 << " : "
                 << allocation.hours
                 << " hours\n";
        }
    }
};

int main() {
    ResourceGovernanceEngine planner;

    /*
     * The case study represents a public-sector digital-service project.
     * The planning engine separates task requirements from resources,
     * allowing assignment decisions to be validated rather than made
     * solely by project-manager intuition.
     */
    planner.addResource({
        "R-101",
        "Asha Rao",
        ResourceType::Person,
        40.0,
        75.0,
        {"backend", "api", "security", "postgresql"}
    });

    planner.addResource({
        "R-102",
        "Vikram Singh",
        ResourceType::Person,
        40.0,
        68.0,
        {"frontend", "javascript", "accessibility"}
    });

    planner.addResource({
        "R-103",
        "Meera Shah",
        ResourceType::Person,
        32.0,
        92.0,
        {"security", "testing", "cloud"}
    });

    planner.addResource({
        "R-104",
        "Load Testing Cluster",
        ResourceType::Equipment,
        80.0,
        25.0,
        {}
    });

    planner.addTask({
        "T-API",
        "Secure citizen-service API",
        72.0,
        1,
        {"backend", "api", "security"}
    });

    planner.addTask({
        "T-WEB",
        "Accessible service portal",
        64.0,
        2,
        {"frontend", "javascript", "accessibility"}
    });

    planner.addTask({
        "T-SEC",
        "Security and resilience validation",
        40.0,
        1,
        {"security", "testing"}
    });

    cout << "Qualified resources for T-SEC:\n";

    for (const auto& resource :
         planner.findQualifiedResources("T-SEC")) {
        cout << "  " << resource.name
             << " at $" << resource.hourlyCost
             << "/hour\n";
    }

    planner.allocate("R-101", "T-API", 72.0);
    planner.allocate("R-102", "T-WEB", 64.0);
    planner.allocate("R-103", "T-SEC", 40.0);

    try {
        /*
         * This request is deliberately rejected because R-101 has already
         * consumed its planned weekly capacity. Capacity enforcement is
         * performed before the allocation enters the system.
         */
        planner.allocate("R-101", "T-SEC", 20.0);
    } catch (const exception& error) {
        cout << "\nRejected allocation: "
             << error.what()
             << '\n';
    }

    planner.printAllocationRegister();
    planner.printCapacityReport();

    cout << "\nPlanned personnel cost: $"
         << fixed
         << setprecision(2)
         << planner.totalCost()
         << '\n';

    /*
     * The model intentionally keeps resource qualification, capacity
     * validation, allocation, and cost calculation separate. This makes
     * policy changes easier to test and prevents a cost report from silently
     * bypassing allocation constraints.
     */
    return 0;
}
