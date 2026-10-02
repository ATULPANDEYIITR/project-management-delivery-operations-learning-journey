/*
 * Activity Identification
 * -----------------------
 * A C++17 case study for identifying project activities and evaluating
 * whether the resulting activity model is structurally usable for planning.
 *
 * Scenario:
 * A business is implementing an operational analytics platform. Before a
 * schedule can be constructed, the project team must identify meaningful
 * activities, classify them, connect dependencies, validate ownership and
 * deliverables, and detect structural problems.
 *
 * Compile:
 *   g++ -std=c++17 -O2 activity_identification.cpp -o activity_identification
 */

#include <algorithm>
#include <iostream>
#include <map>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

enum class ActivityType {
    Task,
    Milestone,
    Review,
    Handoff
};

enum class Priority {
    Low,
    Medium,
    High,
    Critical
};

std::string toString(ActivityType type) {
    switch (type) {
        case ActivityType::Task:
            return "Task";
        case ActivityType::Milestone:
            return "Milestone";
        case ActivityType::Review:
            return "Review";
        case ActivityType::Handoff:
            return "Handoff";
    }

    return "Unknown";
}

std::string toString(Priority priority) {
    switch (priority) {
        case Priority::Low:
            return "Low";
        case Priority::Medium:
            return "Medium";
        case Priority::High:
            return "High";
        case Priority::Critical:
            return "Critical";
    }

    return "Unknown";
}

struct Activity {
    std::string id;
    std::string name;
    std::string description;
    ActivityType type;
    Priority priority;
    std::string owner;
    std::string deliverable;
    int durationDays;
    std::set<std::string> dependencies;
    std::set<std::string> tags;

    bool actionable() const {
        return type == ActivityType::Task ||
               type == ActivityType::Review ||
               type == ActivityType::Handoff;
    }
};

class ActivityRegister {
private:
    std::map<std::string, Activity> activities;

    static std::set<std::string> words(const std::string& text) {
        std::set<std::string> result;
        std::string current;

        for (char character : text) {
            if (std::isalnum(static_cast<unsigned char>(character))) {
                current += static_cast<char>(
                    std::tolower(static_cast<unsigned char>(character))
                );
            } else if (!current.empty()) {
                result.insert(current);
                current.clear();
            }
        }

        if (!current.empty()) {
            result.insert(current);
        }

        return result;
    }

    static double nameSimilarity(
        const std::string& first,
        const std::string& second
    ) {
        const auto firstWords = words(first);
        const auto secondWords = words(second);

        if (firstWords.empty() || secondWords.empty()) {
            return 0.0;
        }

        std::size_t intersection = 0;

        for (const auto& word : firstWords) {
            if (secondWords.count(word)) {
                ++intersection;
            }
        }

        std::set<std::string> unionWords = firstWords;

        unionWords.insert(secondWords.begin(), secondWords.end());

        return static_cast<double>(intersection) /
               static_cast<double>(unionWords.size());
    }

public:
    void add(const Activity& activity) {
        if (activity.id.empty()) {
            throw std::invalid_argument("Activity ID cannot be empty.");
        }

        if (activity.name.empty()) {
            throw std::invalid_argument("Activity name cannot be empty.");
        }

        if (activity.durationDays < 0) {
            throw std::invalid_argument(
                "Activity duration cannot be negative."
            );
        }

        if (activity.type == ActivityType::Milestone &&
            activity.durationDays != 0) {
            throw std::invalid_argument(
                "Milestones must have zero duration."
            );
        }

        if (activities.count(activity.id)) {
            throw std::invalid_argument(
                "Duplicate activity ID: " + activity.id
            );
        }

        // Similar-name detection prevents a project team from accidentally
        // creating two activity records for the same identifiable work.
        for (const auto& [existingId, existing] : activities) {
            if (nameSimilarity(activity.name, existing.name) >= 0.8) {
                throw std::invalid_argument(
                    "Potential duplicate activity: " + activity.name +
                    " resembles " + existing.name
                );
            }
        }

        activities.emplace(activity.id, activity);
    }

    const Activity& get(const std::string& id) const {
        auto iterator = activities.find(id);

        if (iterator == activities.end()) {
            throw std::out_of_range("Unknown activity: " + id);
        }

        return iterator->second;
    }

    const std::map<std::string, Activity>& all() const {
        return activities;
    }

    std::vector<std::string> validate() const {
        std::vector<std::string> errors;

        for (const auto& [id, activity] : activities) {
            for (const auto& dependency : activity.dependencies) {
                if (!activities.count(dependency)) {
                    errors.push_back(
                        id + " references unknown dependency " + dependency
                    );
                }
            }
        }

        if (hasCycle()) {
            errors.push_back(
                "Activity dependency graph contains a cycle."
            );
        }

        return errors;
    }

private:
    bool hasCycle() const {
        enum class VisitState {
            Unvisited,
            Visiting,
            Visited
        };

        std::map<std::string, VisitState> states;

        for (const auto& [id, activity] : activities) {
            states[id] = VisitState::Unvisited;
        }

        std::function<bool(const std::string&)> visit =
            [&](const std::string& id) -> bool {
                if (states[id] == VisitState::Visiting) {
                    return true;
                }

                if (states[id] == VisitState::Visited) {
                    return false;
                }

                states[id] = VisitState::Visiting;

                const auto& activity = activities.at(id);

                for (const auto& dependency : activity.dependencies) {
                    if (activities.count(dependency) &&
                        visit(dependency)) {
                        return true;
                    }
                }

                states[id] = VisitState::Visited;
                return false;
            };

        for (const auto& [id, activity] : activities) {
            if (visit(id)) {
                return true;
            }
        }

        return false;
    }
};

class ActivityGovernanceEngine {
private:
    const ActivityRegister& register_;

public:
    explicit ActivityGovernanceEngine(
        const ActivityRegister& activityRegister
    )
        : register_(activityRegister) {}

    std::vector<std::string> topologicalOrder() const {
        const auto errors = register_.validate();

        if (!errors.empty()) {
            throw std::runtime_error(
                "Cannot construct activity order from invalid model."
            );
        }

        std::map<std::string, int> indegree;
        std::map<std::string, std::vector<std::string>> successors;

        for (const auto& [id, activity] : register_.all()) {
            indegree[id] = static_cast<int>(
                activity.dependencies.size()
            );

            for (const auto& dependency : activity.dependencies) {
                successors[dependency].push_back(id);
            }
        }

        // A priority queue is not required for dependency analysis, but a
        // deterministic lexical queue makes the resulting identification
        // order reproducible across executions.
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

            for (const auto& successor : successors[current]) {
                --indegree[successor];

                if (indegree[successor] == 0) {
                    ready.push(successor);
                }
            }
        }

        if (order.size() != register_.all().size()) {
            throw std::runtime_error(
                "Topological ordering failed."
            );
        }

        return order;
    }

    std::vector<const Activity*> activitiesWithoutOwners() const {
        std::vector<const Activity*> result;

        for (const auto& [id, activity] : register_.all()) {
            if (activity.owner.empty()) {
                result.push_back(&activity);
            }
        }

        return result;
    }

    std::vector<const Activity*> activitiesWithoutDeliverables() const {
        std::vector<const Activity*> result;

        for (const auto& [id, activity] : register_.all()) {
            if (activity.actionable() && activity.deliverable.empty()) {
                result.push_back(&activity);
            }
        }

        return result;
    }

    std::vector<const Activity*> highAttentionActivities() const {
        std::vector<const Activity*> result;

        for (const auto& [id, activity] : register_.all()) {
            if (activity.priority == Priority::High ||
                activity.priority == Priority::Critical ||
                activity.dependencies.size() >= 3) {
                result.push_back(&activity);
            }
        }

        return result;
    }

    std::map<std::string, std::vector<const Activity*>>
    groupByWorkPackage() const {
        std::map<std::string, std::vector<const Activity*>> groups;

        for (const auto& [id, activity] : register_.all()) {
            const std::string package =
                activity.tags.empty()
                    ? "unclassified"
                    : *activity.tags.begin();

            groups[package].push_back(&activity);
        }

        return groups;
    }
};

Activity makeActivity(
    std::string id,
    std::string name,
    std::string description,
    ActivityType type,
    Priority priority,
    std::string owner,
    std::string deliverable,
    int durationDays,
    std::set<std::string> dependencies,
    std::set<std::string> tags
) {
    return Activity{
        std::move(id),
        std::move(name),
        std::move(description),
        type,
        priority,
        std::move(owner),
        std::move(deliverable),
        durationDays,
        std::move(dependencies),
        std::move(tags)
    };
}

ActivityRegister buildAnalyticsProject() {
    ActivityRegister project;

    /*
     * The activity model represents an actual analytics implementation.
     * Each activity exists because it produces a meaningful intermediate
     * result or represents a meaningful project event.
     */
    project.add(makeActivity(
        "ACT-201",
        "Identify operational reporting requirements",
        "Collect and validate reporting needs from operational stakeholders.",
        ActivityType::Task,
        Priority::High,
        "Business Analyst",
        "Validated requirements register",
        3,
        {},
        {"requirements"}
    ));

    project.add(makeActivity(
        "ACT-202",
        "Define analytical data model",
        "Define reporting entities, dimensions, measures, and relationships.",
        ActivityType::Task,
        Priority::High,
        "Data Architect",
        "Approved analytical data model",
        4,
        {"ACT-201"},
        {"data"}
    ));

    project.add(makeActivity(
        "ACT-203",
        "Design dashboard interaction model",
        "Define navigation, filters, drill-downs, and reporting interactions.",
        ActivityType::Task,
        Priority::Medium,
        "Product Designer",
        "Dashboard interaction specification",
        3,
        {"ACT-201"},
        {"design"}
    ));

    project.add(makeActivity(
        "ACT-204",
        "Implement reporting data pipeline",
        "Build extraction, validation, transformation, and loading logic.",
        ActivityType::Task,
        Priority::High,
        "Data Engineer",
        "Validated reporting pipeline",
        6,
        {"ACT-202"},
        {"data"}
    ));

    project.add(makeActivity(
        "ACT-205",
        "Implement operational dashboard",
        "Build dashboard views using the approved data model and interaction design.",
        ActivityType::Task,
        Priority::High,
        "Frontend Engineer",
        "Functional operational dashboard",
        5,
        {"ACT-203", "ACT-204"},
        {"development"}
    ));

    project.add(makeActivity(
        "ACT-206",
        "Validate end-to-end reporting flow",
        "Verify data movement, calculations, filtering, and dashboard behavior.",
        ActivityType::Review,
        Priority::High,
        "QA Engineer",
        "End-to-end validation report",
        4,
        {"ACT-205"},
        {"quality"}
    ));

    project.add(makeActivity(
        "ACT-207",
        "Review operational readiness",
        "Review support, operational, deployment, and ownership readiness.",
        ActivityType::Review,
        Priority::Critical,
        "Release Manager",
        "Operational readiness decision",
        2,
        {"ACT-206"},
        {"release"}
    ));

    project.add(makeActivity(
        "ACT-208",
        "Production readiness milestone",
        "Marks the project event at which operational readiness is formally established.",
        ActivityType::Milestone,
        Priority::Critical,
        "Release Manager",
        "Production readiness milestone",
        0,
        {"ACT-207"},
        {"release"}
    ));

    return project;
}

void printActivityRegister(const ActivityRegister& project) {
    std::cout << "\n=== IDENTIFIED PROJECT ACTIVITIES ===\n";

    for (const auto& [id, activity] : project.all()) {
        std::cout
            << id << " | "
            << activity.name
            << " | type=" << toString(activity.type)
            << " | priority=" << toString(activity.priority)
            << " | owner=" << activity.owner
            << " | duration=" << activity.durationDays
            << " days\n";

        std::cout << "  Deliverable: "
                  << activity.deliverable << '\n';

        std::cout << "  Dependencies: ";

        if (activity.dependencies.empty()) {
            std::cout << "none";
        } else {
            bool first = true;

            for (const auto& dependency : activity.dependencies) {
                if (!first) {
                    std::cout << ", ";
                }

                std::cout << dependency;
                first = false;
            }
        }

        std::cout << '\n';
    }
}

void printValidation(const ActivityRegister& project) {
    std::cout << "\n=== MODEL VALIDATION ===\n";

    const auto errors = project.validate();

    if (errors.empty()) {
        std::cout
            << "The identified activity model has valid dependency references "
               "and no dependency cycle.\n";
        return;
    }

    for (const auto& error : errors) {
        std::cout << "Error: " << error << '\n';
    }
}

void printGovernanceAnalysis(const ActivityRegister& project) {
    ActivityGovernanceEngine engine(project);

    std::cout << "\n=== IDENTIFICATION QUALITY ANALYSIS ===\n";

    const auto ownerGaps = engine.activitiesWithoutOwners();

    std::cout
        << "Activities without an assigned owner: "
        << ownerGaps.size() << '\n';

    const auto deliverableGaps =
        engine.activitiesWithoutDeliverables();

    std::cout
        << "Actionable activities without deliverables: "
        << deliverableGaps.size() << '\n';

    const auto highAttention =
        engine.highAttentionActivities();

    std::cout
        << "High-attention activities: "
        << highAttention.size() << '\n';

    std::cout << "\nWork-package distribution:\n";

    for (const auto& [package, activities] :
         engine.groupByWorkPackage()) {
        std::cout
            << "  " << package
            << ": " << activities.size()
            << " activities\n";
    }
}

void printDependencyOrder(const ActivityRegister& project) {
    ActivityGovernanceEngine engine(project);

    std::cout << "\n=== DEPENDENCY-AWARE ACTIVITY ORDER ===\n";

    for (const auto& id : engine.topologicalOrder()) {
        const auto& activity = project.get(id);

        std::cout
            << id << " | "
            << activity.name
            << " | prerequisites=";

        if (activity.dependencies.empty()) {
            std::cout << "none";
        } else {
            bool first = true;

            for (const auto& dependency :
                 activity.dependencies) {
                if (!first) {
                    std::cout << ", ";
                }

                std::cout << dependency;
                first = false;
            }
        }

        std::cout << '\n';
    }
}

void demonstrateInvalidModels() {
    std::cout << "\n=== INVALID IDENTIFICATION MODELS ===\n";

    ActivityRegister missingDependencyProject;

    missingDependencyProject.add(makeActivity(
        "BAD-001",
        "Build reporting interface",
        "Build the interface without a recognized prerequisite.",
        ActivityType::Task,
        Priority::Medium,
        "Frontend Engineer",
        "Reporting interface",
        4,
        {"UNKNOWN-001"},
        {"development"}
    ));

    for (const auto& error :
         missingDependencyProject.validate()) {
        std::cout << "Detected: " << error << '\n';
    }

    ActivityRegister cyclicProject;

    cyclicProject.add(makeActivity(
        "CYCLE-A",
        "Define release process",
        "Define the release process.",
        ActivityType::Task,
        Priority::Medium,
        "Release Manager",
        "Release process",
        2,
        {"CYCLE-B"},
        {"release"}
    ));

    cyclicProject.add(makeActivity(
        "CYCLE-B",
        "Validate release process",
        "Validate the release process.",
        ActivityType::Review,
        Priority::Medium,
        "QA Engineer",
        "Release validation",
        2,
        {"CYCLE-A"},
        {"release"}
    ));

    for (const auto& error :
         cyclicProject.validate()) {
        std::cout << "Detected: " << error << '\n';
    }
}

int main() {
    try {
        std::cout
            << "PROJECT ACTIVITY IDENTIFICATION ENGINE\n"
            << "=======================================\n";

        const ActivityRegister project =
            buildAnalyticsProject();

        printActivityRegister(project);
        printValidation(project);
        printGovernanceAnalysis(project);
        printDependencyOrder(project);
        demonstrateInvalidModels();

        std::cout
            << "\nActivity identification case study completed.\n";
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }

    return 0;
}
