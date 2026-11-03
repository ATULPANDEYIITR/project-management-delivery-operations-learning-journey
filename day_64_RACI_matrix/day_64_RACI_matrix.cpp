#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

enum class Responsibility {
    Responsible,
    Accountable,
    Consulted,
    Informed
};

char responsibilityCode(Responsibility responsibility) {
    switch (responsibility) {
        case Responsibility::Responsible: return 'R';
        case Responsibility::Accountable: return 'A';
        case Responsibility::Consulted: return 'C';
        case Responsibility::Informed: return 'I';
    }
    throw std::logic_error("Unknown responsibility value.");
}

enum class MatrixStatus {
    Draft,
    Active
};

struct Role {
    std::string code;
    std::string name;
    std::string department;
    std::optional<std::size_t> maxResponsibleTasks;
};

struct WorkItem {
    std::string id;
    std::string title;
    bool securitySensitive = false;
};

class RaciEngine {
public:
    explicit RaciEngine(std::string projectId, std::string projectName)
        : projectId_(std::move(projectId)),
          projectName_(std::move(projectName)) {
        if (projectId_.empty() || projectName_.empty()) {
            throw std::invalid_argument("Project ID and name are required.");
        }
    }

    void addRole(const Role& role) {
        ensureDraft();

        if (role.code.empty() || role.name.empty()) {
            throw std::invalid_argument("Role code and name cannot be empty.");
        }
        if (roles_.count(role.code) != 0) {
            throw std::invalid_argument("Duplicate role code: " + role.code);
        }

        roles_.emplace(role.code, role);
    }

    void addTask(const WorkItem& task) {
        ensureDraft();

        if (task.id.empty() || task.title.empty()) {
            throw std::invalid_argument("Task ID and title cannot be empty.");
        }
        if (tasks_.count(task.id) != 0) {
            throw std::invalid_argument("Duplicate task ID: " + task.id);
        }

        tasks_.emplace(task.id, task);
    }

    void setAssignment(
        const std::string& taskId,
        const std::string& roleCode,
        Responsibility responsibility
    ) {
        ensureDraft();

        if (tasks_.count(taskId) == 0) {
            throw std::invalid_argument("Unknown task: " + taskId);
        }
        if (roles_.count(roleCode) == 0) {
            throw std::invalid_argument("Unknown role: " + roleCode);
        }

        const auto key = std::make_pair(taskId, roleCode);
        const auto old = assignments_.find(key);

        std::string previous = "UNASSIGNED";
        if (old != assignments_.end()) {
            previous = std::string(1, responsibilityCode(old->second));
        }

        assignments_[key] = responsibility;

        std::ostringstream event;
        event << taskId << ": " << roleCode << " changed from "
              << previous << " to " << responsibilityCode(responsibility);
        auditLog_.push_back(event.str());
    }

    std::vector<std::string> validate() const {
        std::vector<std::string> errors;

        if (tasks_.empty()) {
            errors.push_back("The matrix contains no tasks.");
        }

        for (const auto& [taskId, task] : tasks_) {
            std::size_t accountableCount = 0;
            std::size_t responsibleCount = 0;
            bool securityConsulted = false;

            for (const auto& [roleCode, role] : roles_) {
                const auto assignment = assignments_.find(
                    std::make_pair(taskId, roleCode)
                );

                if (assignment == assignments_.end()) {
                    continue;
                }

                if (assignment->second == Responsibility::Accountable) {
                    ++accountableCount;
                } else if (assignment->second == Responsibility::Responsible) {
                    ++responsibleCount;
                }

                if (roleCode == "SECURITY_OFFICER" &&
                    assignment->second == Responsibility::Consulted) {
                    securityConsulted = true;
                }
            }

            if (accountableCount != 1) {
                errors.push_back(
                    taskId + ": expected exactly one A; found " +
                    std::to_string(accountableCount) + "."
                );
            }

            if (responsibleCount == 0) {
                errors.push_back(taskId + ": at least one R is required.");
            }

            if (task.securitySensitive && !securityConsulted) {
                errors.push_back(
                    taskId + ": SECURITY_OFFICER must be assigned C."
                );
            }
        }

        return errors;
    }

    std::vector<std::string> workloadWarnings() const {
        std::map<std::string, std::size_t> workload;

        for (const auto& [key, responsibility] : assignments_) {
            if (responsibility == Responsibility::Responsible) {
                ++workload[key.second];
            }
        }

        std::vector<std::string> warnings;

        for (const auto& [roleCode, role] : roles_) {
            if (!role.maxResponsibleTasks.has_value()) {
                continue;
            }

            const std::size_t count = workload[roleCode];
            if (count > role.maxResponsibleTasks.value()) {
                warnings.push_back(
                    roleCode + ": responsible for " + std::to_string(count) +
                    " tasks; capacity is " +
                    std::to_string(role.maxResponsibleTasks.value()) + "."
                );
            }
        }

        return warnings;
    }

    void publish() {
        ensureDraft();

        const auto errors = validate();
        if (!errors.empty()) {
            std::ostringstream message;
            message << "Publication blocked:";
            for (const auto& error : errors) {
                message << "\n- " << error;
            }
            throw std::runtime_error(message.str());
        }

        status_ = MatrixStatus::Active;
        ++version_;
        auditLog_.push_back("Matrix published at version " +
                            std::to_string(version_));
    }

    void printMatrix() const {
        std::cout << "\nRACI Matrix\n";
        std::cout << std::left << std::setw(34) << "Work item";

        for (const auto& [code, role] : roles_) {
            std::cout << " | " << std::setw(14) << code;
        }
        std::cout << '\n';

        std::cout << std::string(34 + roles_.size() * 17, '-') << '\n';

        for (const auto& [taskId, task] : tasks_) {
            std::cout << std::left
                      << std::setw(34)
                      << (taskId + ": " + task.title);

            for (const auto& [roleCode, role] : roles_) {
                const auto assignment = assignments_.find(
                    std::make_pair(taskId, roleCode)
                );

                const std::string value =
                    assignment == assignments_.end()
                    ? "-"
                    : std::string(1, responsibilityCode(assignment->second));

                std::cout << " | " << std::setw(14) << value;
            }
            std::cout << '\n';
        }
    }

    void printWorkload() const {
        std::map<std::string, std::map<char, std::size_t>> counts;

        for (const auto& [roleCode, role] : roles_) {
            counts[roleCode] = {{'R', 0}, {'A', 0}, {'C', 0}, {'I', 0}};
        }

        for (const auto& [key, responsibility] : assignments_) {
            ++counts[key.second][responsibilityCode(responsibility)];
        }

        std::cout << "\nRole workload\n";
        for (const auto& [roleCode, roleCounts] : counts) {
            std::cout << roleCode
                      << ": R=" << roleCounts.at('R')
                      << ", A=" << roleCounts.at('A')
                      << ", C=" << roleCounts.at('C')
                      << ", I=" << roleCounts.at('I') << '\n';
        }
    }

    MatrixStatus status() const {
        return status_;
    }

    std::size_t version() const {
        return version_;
    }

    const std::vector<std::string>& auditLog() const {
        return auditLog_;
    }

private:
    std::string projectId_;
    std::string projectName_;
    std::map<std::string, Role> roles_;
    std::map<std::string, WorkItem> tasks_;

    // Each task-role pair has one code. Reassignment replaces that code.
    std::map<std::pair<std::string, std::string>, Responsibility> assignments_;

    MatrixStatus status_ = MatrixStatus::Draft;
    std::size_t version_ = 1;
    std::vector<std::string> auditLog_;

    void ensureDraft() const {
        if (status_ != MatrixStatus::Draft) {
            throw std::logic_error("An active matrix cannot be modified.");
        }
    }
};

RaciEngine buildCloudMigrationMatrix() {
    RaciEngine engine("PRJ-100", "Cloud Infrastructure Migration");

    engine.addRole({"SPONSOR", "Project Sponsor", "Executive Office", std::nullopt});
    engine.addRole({"PM", "Project Manager", "Program Management", std::nullopt});
    engine.addRole({"ARCHITECT", "Cloud Architect", "Technology", 2});
    engine.addRole({
        "SECURITY_OFFICER",
        "Security Officer",
        "Information Security",
        std::nullopt
    });
    engine.addRole({"QA", "Quality Lead", "Quality Assurance", std::nullopt});
    engine.addRole({"OPERATIONS", "Operations Lead", "IT Operations", 2});

    engine.addTask({"T1", "Inventory and discovery", false});
    engine.addTask({"T2", "Target architecture approval", true});
    engine.addTask({"T3", "Production migration", true});
    engine.addTask({"T4", "Acceptance testing", false});

    using R = Responsibility;

    const std::vector<std::tuple<std::string, std::string, R>> assignments = {
        {"T1", "SPONSOR", R::Accountable},
        {"T1", "PM", R::Responsible},
        {"T1", "ARCHITECT", R::Consulted},
        {"T1", "SECURITY_OFFICER", R::Informed},
        {"T1", "QA", R::Informed},
        {"T1", "OPERATIONS", R::Consulted},

        {"T2", "SPONSOR", R::Informed},
        {"T2", "PM", R::Accountable},
        {"T2", "ARCHITECT", R::Responsible},
        {"T2", "SECURITY_OFFICER", R::Consulted},
        {"T2", "QA", R::Informed},
        {"T2", "OPERATIONS", R::Consulted},

        {"T3", "SPONSOR", R::Informed},
        {"T3", "PM", R::Accountable},
        {"T3", "ARCHITECT", R::Responsible},
        {"T3", "SECURITY_OFFICER", R::Consulted},
        {"T3", "QA", R::Informed},
        {"T3", "OPERATIONS", R::Responsible},

        {"T4", "SPONSOR", R::Informed},
        {"T4", "PM", R::Accountable},
        {"T4", "ARCHITECT", R::Informed},
        {"T4", "SECURITY_OFFICER", R::Informed},
        {"T4", "QA", R::Responsible},
        {"T4", "OPERATIONS", R::Consulted}
    };

    for (const auto& [taskId, roleCode, responsibility] : assignments) {
        engine.setAssignment(taskId, roleCode, responsibility);
    }

    return engine;
}

void demonstrateInvalidMatrix() {
    RaciEngine incomplete("PRJ-200", "Incomplete Payment Platform");

    incomplete.addRole({"PM", "Project Manager", "Delivery", std::nullopt});
    incomplete.addRole({"DEV", "Developer", "Engineering", std::nullopt});
    incomplete.addRole({
        "SECURITY_OFFICER",
        "Security Officer",
        "Security",
        std::nullopt
    });
    incomplete.addTask({"P1", "Payment security review", true});

    incomplete.setAssignment("P1", "DEV", Responsibility::Responsible);
    incomplete.setAssignment("P1", "SECURITY_OFFICER", Responsibility::Informed);

    try {
        incomplete.publish();
    } catch (const std::exception& error) {
        std::cout << "\nExpected publication failure:\n"
                  << error.what() << '\n';
    }
}

int main() {
    try {
        RaciEngine engine = buildCloudMigrationMatrix();

        const auto errors = engine.validate();
        if (!errors.empty()) {
            throw std::runtime_error("Unexpected invalid demonstration matrix.");
        }

        engine.printMatrix();
        engine.printWorkload();

        const auto warnings = engine.workloadWarnings();
        std::cout << "\nWorkload warnings:\n";

        if (warnings.empty()) {
            std::cout << "None\n";
        } else {
            for (const auto& warning : warnings) {
                std::cout << "- " << warning << '\n';
            }
        }

        engine.publish();

        std::cout << "\nStatus: "
                  << (engine.status() == MatrixStatus::Active ? "ACTIVE" : "DRAFT")
                  << "\nVersion: " << engine.version() << '\n';

        try {
            engine.setAssignment(
                "T1",
                "PM",
                Responsibility::Accountable
            );
        } catch (const std::exception& error) {
            std::cout << "\nExpected modification failure: "
                      << error.what() << '\n';
        }

        std::cout << "\nAudit events: " << engine.auditLog().size() << '\n';

        demonstrateInvalidMatrix();
    } catch (const std::exception& error) {
        std::cerr << "Execution failed: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
