#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <queue>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

enum class ResourceType {
    Compute,
    Memory,
    Storage,
    DatabaseConnections
};

std::string toString(ResourceType type) {
    switch (type) {
        case ResourceType::Compute: return "compute";
        case ResourceType::Memory: return "memory";
        case ResourceType::Storage: return "storage";
        case ResourceType::DatabaseConnections: return "database_connections";
    }
    throw std::logic_error("Unknown resource type");
}

struct Requirement {
    ResourceType type;
    int amount;
};

class ResourcePool {
private:
    std::string name_;
    int capacity_;
    int available_;
    std::unordered_map<std::string, int> allocations_;

public:
    ResourcePool(std::string name, int capacity)
        : name_(std::move(name)),
          capacity_(capacity),
          available_(capacity) {
        if (capacity <= 0) {
            throw std::invalid_argument("Capacity must be positive");
        }
    }

    bool canAllocate(int amount) const {
        return amount > 0 && amount <= available_;
    }

    bool allocate(const std::string& owner, int amount) {
        if (!canAllocate(amount)) {
            return false;
        }

        available_ -= amount;
        allocations_[owner] += amount;
        return true;
    }

    int release(const std::string& owner) {
        auto it = allocations_.find(owner);
        if (it == allocations_.end()) {
            return 0;
        }

        const int released = it->second;
        available_ += released;
        allocations_.erase(it);
        return released;
    }

    int available() const {
        return available_;
    }

    int capacity() const {
        return capacity_;
    }

    double utilization() const {
        return static_cast<double>(capacity_ - available_) / capacity_;
    }

    const std::string& name() const {
        return name_;
    }
};

class GovernanceResourceManager {
private:
    std::map<ResourceType, ResourcePool> pools_;

public:
    void addPool(ResourceType type, const std::string& name, int capacity) {
        if (pools_.contains(type)) {
            throw std::logic_error("Duplicate resource pool");
        }

        pools_.emplace(
            std::piecewise_construct,
            std::forward_as_tuple(type),
            std::forward_as_tuple(name, capacity)
        );
    }

    /*
     * The admission operation is transactional:
     * every requirement is checked before any pool is modified.
     * This prevents a job from receiving CPU while failing to receive
     * its required memory, leaving capacity in an inconsistent state.
     */
    bool request(
        const std::string& owner,
        const std::vector<Requirement>& requirements
    ) {
        if (owner.empty()) {
            throw std::invalid_argument("Owner cannot be empty");
        }

        std::map<ResourceType, int> totals;

        for (const auto& requirement : requirements) {
            if (requirement.amount <= 0) {
                throw std::invalid_argument("Requirement must be positive");
            }

            totals[requirement.type] += requirement.amount;
        }

        for (const auto& [type, amount] : totals) {
            auto it = pools_.find(type);

            if (it == pools_.end()) {
                throw std::out_of_range("Requested resource pool does not exist");
            }

            if (!it->second.canAllocate(amount)) {
                return false;
            }
        }

        for (const auto& [type, amount] : totals) {
            pools_.at(type).allocate(owner, amount);
        }

        return true;
    }

    int release(const std::string& owner) {
        int total = 0;

        for (auto& [type, pool] : pools_) {
            total += pool.release(owner);
        }

        return total;
    }

    void printReport() const {
        std::cout << std::left
                  << std::setw(25) << "Pool"
                  << std::setw(14) << "Capacity"
                  << std::setw(14) << "Available"
                  << "Utilization\n";

        for (const auto& [type, pool] : pools_) {
            std::cout << std::left
                      << std::setw(25) << pool.name()
                      << std::setw(14) << pool.capacity()
                      << std::setw(14) << pool.available()
                      << std::fixed << std::setprecision(1)
                      << pool.utilization() * 100 << "%\n";
        }
    }
};

struct Workload {
    std::string id;
    std::string owner;
    int priority;
    std::vector<Requirement> requirements;
};

struct HigherPriority {
    bool operator()(const Workload& left, const Workload& right) const {
        return left.priority < right.priority;
    }
};

class CapacityScheduler {
private:
    GovernanceResourceManager& manager_;
    std::priority_queue<
        Workload,
        std::vector<Workload>,
        HigherPriority
    > queue_;

public:
    explicit CapacityScheduler(GovernanceResourceManager& manager)
        : manager_(manager) {}

    void submit(Workload workload) {
        if (workload.id.empty() || workload.owner.empty()) {
            throw std::invalid_argument("Workload identity is required");
        }

        queue_.push(std::move(workload));
    }

    std::vector<std::string> dispatch() {
        std::vector<std::string> started;
        std::vector<Workload> deferred;

        while (!queue_.empty()) {
            Workload workload = queue_.top();
            queue_.pop();

            if (manager_.request(workload.owner, workload.requirements)) {
                started.push_back(workload.id);
            } else {
                /*
                 * A workload that cannot fit now remains queued. A production
                 * scheduler would normally also use aging, deadlines,
                 * starvation protection, and resource-specific placement.
                 */
                deferred.push_back(std::move(workload));
            }
        }

        for (auto& workload : deferred) {
            queue_.push(std::move(workload));
        }

        return started;
    }

    std::size_t pending() const {
        return queue_.size();
    }
};

void demonstrateAtomicAdmission() {
    GovernanceResourceManager manager;

    manager.addPool(ResourceType::Compute, "Application CPU", 16);
    manager.addPool(ResourceType::Memory, "Application RAM", 64);
    manager.addPool(ResourceType::Storage, "Object Storage", 1000);
    manager.addPool(
        ResourceType::DatabaseConnections,
        "Database Connections",
        30
    );

    const bool accepted = manager.request(
        "analytics-service",
        {
            {ResourceType::Compute, 6},
            {ResourceType::Memory, 24},
            {ResourceType::DatabaseConnections, 5}
        }
    );

    std::cout << "Analytics workload accepted: "
              << std::boolalpha << accepted << "\n";

    const bool rejected = manager.request(
        "large-batch",
        {
            {ResourceType::Compute, 4},
            {ResourceType::Memory, 100}
        }
    );

    std::cout << "Large batch accepted: "
              << rejected << "\n";

    std::cout << "\nCapacity after requests:\n";
    manager.printReport();

    manager.release("analytics-service");

    std::cout << "\nCapacity after workload completion:\n";
    manager.printReport();
}

void demonstratePriorityScheduling() {
    GovernanceResourceManager manager;

    manager.addPool(ResourceType::Compute, "Workers", 8);
    manager.addPool(ResourceType::Memory, "Worker RAM", 32);

    CapacityScheduler scheduler(manager);

    scheduler.submit({
        "nightly-report",
        "reporting",
        10,
        {
            {ResourceType::Compute, 3},
            {ResourceType::Memory, 8}
        }
    });

    scheduler.submit({
        "production-recovery",
        "operations",
        100,
        {
            {ResourceType::Compute, 5},
            {ResourceType::Memory, 16}
        }
    });

    auto started = scheduler.dispatch();

    std::cout << "\nStarted workloads:\n";
    for (const auto& id : started) {
        std::cout << "  " << id << "\n";
    }

    std::cout << "Pending workloads: " << scheduler.pending() << "\n";

    manager.release("operations");

    auto later = scheduler.dispatch();

    std::cout << "Started after capacity release:\n";
    for (const auto& id : later) {
        std::cout << "  " << id << "\n";
    }
}

void demonstrateCapacityTradeoffs() {
    GovernanceResourceManager manager;

    manager.addPool(ResourceType::Compute, "Shared Compute", 100);

    manager.request(
        "service-a",
        {{ResourceType::Compute, 70}}
    );

    std::cout << "\nUtilization after service-a: ";
    manager.printReport();

    /*
     * A high utilization value is not automatically bad. Capacity planning
     * must consider workload variability, latency targets, burst demand,
     * recovery capacity, and the cost of idle resources.
     */
}

int main() {
    try {
        std::cout << "=== Atomic Resource Admission ===\n";
        demonstrateAtomicAdmission();

        std::cout << "\n=== Priority Scheduling ===\n";
        demonstratePriorityScheduling();

        std::cout << "\n=== Capacity Planning Metric ===\n";
        demonstrateCapacityTradeoffs();

    } catch (const std::exception& error) {
        std::cerr << "Resource management error: "
                  << error.what() << '\n';
        return 1;
    }

    return 0;
}
