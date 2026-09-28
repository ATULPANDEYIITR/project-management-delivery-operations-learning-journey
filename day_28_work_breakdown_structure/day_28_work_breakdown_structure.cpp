/*
    WORK BREAKDOWN STRUCTURE (WBS)
    Breaking Work into Smaller Parts

    Comprehensive C++17 case study:
    Enterprise Customer Portal Project Planning System

    Demonstrates:
    - WBS hierarchy
    - deliverables and work packages
    - decomposition
    - WBS dictionary information
    - cost and effort roll-up
    - dependency graph
    - topological sorting
    - earliest-start scheduling
    - critical-path calculation
    - resource planning
    - risk analysis
    - requirement traceability
    - change control
    - earned value management
    - validation
    - complexity considerations

    Compile:
        g++ -std=c++17 -O2 wbs.cpp -o wbs

    Run:
        ./wbs
*/

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;


// ============================================================================
// 1. GENERAL OUTPUT HELPERS
// ============================================================================

void printSection(const string& title) {
    cout << "\n" << string(78, '=') << "\n";
    cout << title << "\n";
    cout << string(78, '=') << "\n";
}

void printSubsection(const string& title) {
    cout << "\n" << string(78, '-') << "\n";
    cout << title << "\n";
    cout << string(78, '-') << "\n";
}

string formatCurrency(double value) {
    ostringstream output;
    output << "$" << fixed << setprecision(2) << value;
    return output.str();
}


// ============================================================================
// 2. WBS NODE
// ============================================================================

struct WBSNode {
    string code;
    string name;
    int level;
    string type;
    string description;

    double durationDays = 0.0;
    double cost = 0.0;

    string owner;
    string parentCode;

    vector<string> children;
    vector<string> dependencies;
    vector<string> acceptanceCriteria;

    bool isLeaf() const {
        return children.empty();
    }
};


// ============================================================================
// 3. WBS CLASS
// ============================================================================

class WBS {
private:
    string projectName;
    map<string, WBSNode> nodes;

public:
    explicit WBS(string name)
        : projectName(move(name)) {}

    const string& getProjectName() const {
        return projectName;
    }

    void addNode(const WBSNode& node) {
        if (nodes.count(node.code) != 0) {
            throw invalid_argument(
                "Duplicate WBS code: " + node.code
            );
        }

        if (!node.parentCode.empty()) {
            auto parent = nodes.find(node.parentCode);

            if (parent == nodes.end()) {
                throw invalid_argument(
                    "Missing parent " + node.parentCode +
                    " for " + node.code
                );
            }

            const int expectedLevel = parent->second.level + 1;

            if (node.level != expectedLevel) {
                throw invalid_argument(
                    "Invalid level for " + node.code
                );
            }
        }

        nodes[node.code] = node;

        if (!node.parentCode.empty()) {
            nodes[node.parentCode].children.push_back(node.code);
        }
    }

    WBSNode& getNode(const string& code) {
        auto iterator = nodes.find(code);

        if (iterator == nodes.end()) {
            throw out_of_range(
                "Unknown WBS code: " + code
            );
        }

        return iterator->second;
    }

    const WBSNode& getNode(const string& code) const {
        auto iterator = nodes.find(code);

        if (iterator == nodes.end()) {
            throw out_of_range(
                "Unknown WBS code: " + code
            );
        }

        return iterator->second;
    }

    vector<WBSNode> getDirectChildren(const string& code) const {
        const WBSNode& node = getNode(code);
        vector<WBSNode> result;

        for (const string& child : node.children) {
            result.push_back(getNode(child));
        }

        return result;
    }

    vector<WBSNode> getLeaves() const {
        vector<WBSNode> result;

        for (const auto& [code, node] : nodes) {
            if (node.isLeaf()) {
                result.push_back(node);
            }
        }

        return result;
    }

    size_t size() const {
        return nodes.size();
    }

    void printTree() const {
        vector<string> roots;

        for (const auto& [code, node] : nodes) {
            if (node.parentCode.empty()) {
                roots.push_back(code);
            }
        }

        if (roots.size() != 1) {
            throw runtime_error(
                "A project WBS should contain exactly one root."
            );
        }

        function<void(const string&, const string&)> visit =
            [&](const string& code, const string& prefix) {
                const WBSNode& node = getNode(code);

                cout << prefix
                     << node.code
                     << " | "
                     << node.name
                     << " ["
                     << node.type
                     << "]\n";

                for (const string& child : node.children) {
                    visit(child, prefix + "    ");
                }
            };

        visit(roots.front(), "");
    }

    double rollupCost(const string& code) const {
        const WBSNode& node = getNode(code);

        if (node.isLeaf()) {
            return node.cost;
        }

        double total = 0.0;

        for (const string& child : node.children) {
            total += rollupCost(child);
        }

        return total;
    }

    double rollupEffort(const string& code) const {
        const WBSNode& node = getNode(code);

        if (node.isLeaf()) {
            return node.durationDays;
        }

        double total = 0.0;

        for (const string& child : node.children) {
            total += rollupEffort(child);
        }

        return total;
    }

    vector<WBSNode> search(const string& query) const {
        vector<WBSNode> results;

        for (const auto& [code, node] : nodes) {
            if (
                code.find(query) != string::npos ||
                node.name.find(query) != string::npos ||
                node.description.find(query) != string::npos
            ) {
                results.push_back(node);
            }
        }

        return results;
    }

    const map<string, WBSNode>& allNodes() const {
        return nodes;
    }
};


// ============================================================================
// 4. DEPENDENCY GRAPH
// ============================================================================

class DependencyGraph {
private:
    map<string, vector<string>> dependencies;

public:
    void setDependencies(
        const string& task,
        const vector<string>& predecessors
    ) {
        dependencies[task] = predecessors;
    }

    const vector<string>& getDependencies(
        const string& task
    ) const {
        static const vector<string> empty;

        auto iterator = dependencies.find(task);

        if (iterator == dependencies.end()) {
            return empty;
        }

        return iterator->second;
    }

    const map<string, vector<string>>& allDependencies() const {
        return dependencies;
    }

    vector<string> topologicalSort(
        const map<string, double>& durations
    ) const {
        map<string, int> indegree;
        map<string, vector<string>> outgoing;

        for (const auto& [task, duration] : durations) {
            (void)duration;
            indegree[task] = 0;
            outgoing[task] = {};
        }

        for (const auto& [task, predecessors] : dependencies) {
            if (!durations.count(task)) {
                continue;
            }

            for (const string& predecessor : predecessors) {
                if (!durations.count(predecessor)) {
                    throw invalid_argument(
                        "Unknown dependency " +
                        predecessor +
                        " for " +
                        task
                    );
                }

                ++indegree[task];
                outgoing[predecessor].push_back(task);
            }
        }

        priority_queue<
            string,
            vector<string>,
            greater<string>
        > ready;

        for (const auto& [task, degree] : indegree) {
            if (degree == 0) {
                ready.push(task);
            }
        }

        vector<string> order;

        while (!ready.empty()) {
            string current = ready.top();
            ready.pop();

            order.push_back(current);

            for (const string& successor : outgoing[current]) {
                --indegree[successor];

                if (indegree[successor] == 0) {
                    ready.push(successor);
                }
            }
        }

        if (order.size() != durations.size()) {
            throw runtime_error(
                "Dependency graph contains a cycle."
            );
        }

        return order;
    }
};


// ============================================================================
// 5. RISK MODEL
// ============================================================================

struct Risk {
    string name;
    double probability;
    double impactCost;
    double mitigationCost;

    double expectedMonetaryValue() const {
        return probability * impactCost;
    }
};


// ============================================================================
// 6. RESOURCE MODEL
// ============================================================================

struct Resource {
    string name;
    string role;
    double capacityPercent;
    double dailyCost;

    void validate() const {
        if (
            capacityPercent <= 0 ||
            capacityPercent > 100
        ) {
            throw invalid_argument(
                "Resource capacity must be in (0, 100]."
            );
        }

        if (dailyCost < 0) {
            throw invalid_argument(
                "Resource daily cost cannot be negative."
            );
        }
    }
};


// ============================================================================
// 7. CHANGE REQUEST
// ============================================================================

struct ChangeRequest {
    string id;
    string description;
    double estimatedCost;
    double estimatedDurationDays;
    string reason;
    string status;
};


// ============================================================================
// 8. EARNED VALUE
// ============================================================================

struct EarnedValue {
    double plannedValue;
    double earnedValue;
    double actualCost;

    double costVariance() const {
        return earnedValue - actualCost;
    }

    double scheduleVariance() const {
        return earnedValue - plannedValue;
    }

    double costPerformanceIndex() const {
        if (actualCost == 0.0) {
            return numeric_limits<double>::infinity();
        }

        return earnedValue / actualCost;
    }

    double schedulePerformanceIndex() const {
        if (plannedValue == 0.0) {
            return numeric_limits<double>::infinity();
        }

        return earnedValue / plannedValue;
    }
};


// ============================================================================
// 9. BUILD PROJECT WBS
// ============================================================================

WBS buildProjectWBS() {
    WBS wbs("Enterprise Customer Portal");

    wbs.addNode({
        "1",
        "Enterprise Customer Portal",
        1,
        "Project",
        "Complete customer-facing web platform.",
        0,
        0,
        "",
        "",
        {},
        {},
        {}
    });

    vector<tuple<string, string, string>> deliverables = {
        {"1.1", "Project Management", "Management and governance"},
        {"1.2", "User Experience", "Research and interface design"},
        {"1.3", "Application Platform", "Core software capabilities"},
        {"1.4", "Security", "Security engineering"},
        {"1.5", "Quality Assurance", "Testing and quality validation"},
        {"1.6", "Deployment", "Production readiness and release"}
    };

    for (const auto& [code, name, description] : deliverables) {
        wbs.addNode({
            code,
            name,
            2,
            "Deliverable",
            description,
            0,
            0,
            "",
            "1",
            {},
            {},
            {}
        });
    }


    // ------------------------------------------------------------------------
    // Project Management
    // ------------------------------------------------------------------------

    for (const auto& [code, name] : vector<pair<string, string>>{
        {"1.1.1", "Project Planning"},
        {"1.1.2", "Stakeholder Management"},
        {"1.1.3", "Progress Control"}
    }) {
        wbs.addNode({
            code,
            name,
            3,
            "Sub-deliverable",
            "",
            0,
            0,
            "",
            "1.1",
            {},
            {},
            {}
        });
    }

    struct Package {
        string code;
        string name;
        double duration;
        double cost;
    };

    vector<Package> management = {
        {"1.1.1.1", "Create Project Charter", 2, 800},
        {"1.1.1.2", "Create Management Plan", 3, 1200},
        {"1.1.2.1", "Identify Stakeholders", 2, 600},
        {"1.1.2.2", "Create Communication Matrix", 2, 500},
        {"1.1.3.1", "Weekly Status Reporting", 20, 4000},
        {"1.1.3.2", "Change Control", 10, 2500}
    };

    // ------------------------------------------------------------------------
    // User Experience
    // ------------------------------------------------------------------------

    for (const auto& [code, name] : vector<pair<string, string>>{
        {"1.2.1", "User Research"},
        {"1.2.2", "Interaction Design"},
        {"1.2.3", "Visual Design"}
    }) {
        wbs.addNode({
            code,
            name,
            3,
            "Sub-deliverable",
            "",
            0,
            0,
            "",
            "1.2",
            {},
            {},
            {}
        });
    }

    vector<Package> ux = {
        {"1.2.1.1", "Interview Users", 5, 2000},
        {"1.2.1.2", "Analyze User Needs", 4, 1800},
        {"1.2.2.1", "Create User Flows", 4, 1600},
        {"1.2.2.2", "Create Wireframes", 6, 2400},
        {"1.2.3.1", "Create Design System", 7, 3500},
        {"1.2.3.2", "Create High-Fidelity Screens", 8, 4200}
    };

    // ------------------------------------------------------------------------
    // Application Platform
    // ------------------------------------------------------------------------

    for (const auto& [code, name] : vector<pair<string, string>>{
        {"1.3.1", "Authentication"},
        {"1.3.2", "Customer Profile"},
        {"1.3.3", "Dashboard"},
        {"1.3.4", "Notification Service"}
    }) {
        wbs.addNode({
            code,
            name,
            3,
            "Sub-deliverable",
            "",
            0,
            0,
            "",
            "1.3",
            {},
            {},
            {}
        });
    }

    vector<Package> application = {
        {"1.3.1.1", "Login and Logout", 5, 4500},
        {"1.3.1.2", "Password Recovery", 4, 3200},
        {"1.3.1.3", "Multi-Factor Authentication", 7, 6500},
        {"1.3.2.1", "Profile API", 6, 5200},
        {"1.3.2.2", "Profile Interface", 5, 4100},
        {"1.3.3.1", "Dashboard API", 7, 6200},
        {"1.3.3.2", "Dashboard Interface", 7, 5800},
        {"1.3.4.1", "Email Notification Service", 6, 5000},
        {"1.3.4.2", "In-App Notification Service", 5, 4200}
    };

    // ------------------------------------------------------------------------
    // Security
    // ------------------------------------------------------------------------

    for (const auto& [code, name] : vector<pair<string, string>>{
        {"1.4.1", "Security Architecture"},
        {"1.4.2", "Application Security"},
        {"1.4.3", "Security Verification"}
    }) {
        wbs.addNode({
            code,
            name,
            3,
            "Sub-deliverable",
            "",
            0,
            0,
            "",
            "1.4",
            {},
            {},
            {}
        });
    }

    vector<Package> security = {
        {"1.4.1.1", "Threat Modeling", 5, 4000},
        {"1.4.1.2", "Security Requirements", 4, 3000},
        {"1.4.2.1", "Input Validation Controls", 6, 4500},
        {"1.4.2.2", "Authorization Controls", 6, 5000},
        {"1.4.3.1", "Security Test Suite", 7, 5500},
        {"1.4.3.2", "Vulnerability Assessment", 6, 6500}
    };

    // ------------------------------------------------------------------------
    // Quality Assurance
    // ------------------------------------------------------------------------

    for (const auto& [code, name] : vector<pair<string, string>>{
        {"1.5.1", "Test Planning"},
        {"1.5.2", "Functional Testing"},
        {"1.5.3", "Performance Testing"}
    }) {
        wbs.addNode({
            code,
            name,
            3,
            "Sub-deliverable",
            "",
            0,
            0,
            "",
            "1.5",
            {},
            {},
            {}
        });
    }

    vector<Package> qa = {
        {"1.5.1.1", "Test Strategy", 3, 1800},
        {"1.5.1.2", "Test Cases", 6, 3200},
        {"1.5.2.1", "Integration Testing", 8, 6000},
        {"1.5.2.2", "System Testing", 8, 6000},
        {"1.5.3.1", "Load Testing", 5, 4000},
        {"1.5.3.2", "Performance Analysis", 4, 3000}
    };

    // ------------------------------------------------------------------------
    // Deployment
    // ------------------------------------------------------------------------

    for (const auto& [code, name] : vector<pair<string, string>>{
        {"1.6.1", "Infrastructure"},
        {"1.6.2", "Release Engineering"},
        {"1.6.3", "Operational Readiness"}
    }) {
        wbs.addNode({
            code,
            name,
            3,
            "Sub-deliverable",
            "",
            0,
            0,
            "",
            "1.6",
            {},
            {},
            {}
        });
    }

    vector<Package> deployment = {
        {"1.6.1.1", "Production Infrastructure", 5, 6000},
        {"1.6.1.2", "Monitoring Infrastructure", 4, 3500},
        {"1.6.2.1", "CI/CD Pipeline", 6, 5000},
        {"1.6.2.2", "Production Release", 2, 2500},
        {"1.6.3.1", "Operations Runbook", 4, 2200},
        {"1.6.3.2", "Production Readiness Review", 2, 1500}
    };

    vector<vector<Package>> allPackageGroups = {
        management,
        ux,
        application,
        security,
        qa,
        deployment
    };

    for (const auto& group : allPackageGroups) {
        for (const Package& package : group) {
            const size_t separator = package.code.rfind('.');

            if (separator == string::npos) {
                throw runtime_error(
                    "Invalid work-package code: " + package.code
                );
            }

            const string parent =
                package.code.substr(0, separator);

            wbs.addNode({
                package.code,
                package.name,
                4,
                "Work Package",
                "",
                package.duration,
                package.cost,
                "",
                parent,
                {},
                {},
                {}
            });
        }
    }

    return wbs;
}


// ============================================================================
// 10. MAIN CASE STUDY
// ============================================================================

int main() {
    try {
        printSection("WORK BREAKDOWN STRUCTURE CASE STUDY");

        WBS wbs = buildProjectWBS();

        cout << "\nWBS hierarchy:\n";
        wbs.printTree();


        // --------------------------------------------------------------------
        // COST ROLL-UP
        // --------------------------------------------------------------------

        printSection("1. COST ROLL-UP");

        double totalCost = wbs.rollupCost("1");

        for (const WBSNode& deliverable :
             wbs.getDirectChildren("1")) {

            cout << left
                 << setw(8) << deliverable.code
                 << setw(28) << deliverable.name
                 << formatCurrency(
                     wbs.rollupCost(deliverable.code)
                 )
                 << "\n";
        }

        cout << "\nTotal project budget: "
             << formatCurrency(totalCost)
             << "\n";


        // --------------------------------------------------------------------
        // EFFORT ROLL-UP
        // --------------------------------------------------------------------

        printSection("2. EFFORT ROLL-UP");

        const double totalEffort =
            wbs.rollupEffort("1");

        cout << "Total estimated person-days: "
             << totalEffort
             << "\n";

        cout <<
            "\nEffort is not calendar duration. "
            "Parallel work can cause elapsed duration to be smaller "
            "than the sum of all work-package durations.\n";


        // --------------------------------------------------------------------
        // DEPENDENCY GRAPH
        // --------------------------------------------------------------------

        printSection("3. DEPENDENCY GRAPH");

        DependencyGraph graph;

        auto set = [&](const string& task,
                       initializer_list<string> predecessors) {
            graph.setDependencies(
                task,
                vector<string>(predecessors)
            );
        };

        set("1.2.1.1", {});
        set("1.2.1.2", {"1.2.1.1"});
        set("1.2.2.1", {"1.2.1.2"});
        set("1.2.2.2", {"1.2.2.1"});
        set("1.2.3.1", {"1.2.2.2"});
        set("1.2.3.2", {"1.2.3.1"});

        set("1.3.1.1", {"1.2.2.2"});
        set("1.3.1.2", {"1.3.1.1"});
        set("1.3.1.3", {"1.3.1.1"});
        set("1.3.2.1", {"1.2.2.2"});
        set("1.3.2.2", {"1.3.2.1", "1.2.3.2"});
        set("1.3.3.1", {"1.3.2.1"});
        set("1.3.3.2", {"1.3.3.1", "1.2.3.2"});
        set("1.3.4.1", {"1.3.1.1"});
        set("1.3.4.2", {"1.3.1.1"});

        set("1.4.1.1", {});
        set("1.4.1.2", {"1.4.1.1"});
        set("1.4.2.1", {"1.4.1.2"});
        set("1.4.2.2", {"1.4.1.2"});
        set("1.4.3.1", {"1.4.2.1", "1.4.2.2"});
        set("1.4.3.2", {"1.4.3.1"});

        set("1.5.1.1", {});
        set("1.5.1.2", {"1.5.1.1"});
        set(
            "1.5.2.1",
            {"1.5.1.2", "1.3.2.2", "1.3.3.2"}
        );
        set("1.5.2.2", {"1.5.2.1"});
        set("1.5.3.1", {"1.5.2.2"});
        set("1.5.3.2", {"1.5.3.1"});

        set("1.6.1.1", {"1.3.3.2"});
        set("1.6.1.2", {"1.6.1.1"});
        set("1.6.2.1", {"1.6.1.1"});
        set(
            "1.6.2.2",
            {"1.5.2.2", "1.4.3.2", "1.6.2.1"}
        );
        set("1.6.3.1", {"1.6.2.1"});
        set(
            "1.6.3.2",
            {"1.6.2.2", "1.6.3.1"}
        );


        // --------------------------------------------------------------------
        // DURATION MAP
        // --------------------------------------------------------------------

        map<string, double> durations;

        for (const WBSNode& node : wbs.getLeaves()) {
            durations[node.code] = node.durationDays;
        }

        vector<string> order =
            graph.topologicalSort(durations);

        cout << "Dependency-safe order:\n";

        for (const string& task : order) {
            cout << "  "
                 << task
                 << " - "
                 << wbs.getNode(task).name
                 << "\n";
        }


        // --------------------------------------------------------------------
        // EARLIEST START / FINISH
        // --------------------------------------------------------------------

        printSection("4. EARLIEST SCHEDULE");

        map<string, double> earliestStart;
        map<string, double> earliestFinish;

        for (const string& task : order) {
            const vector<string>& predecessors =
                graph.getDependencies(task);

            double start = 0.0;

            for (const string& predecessor : predecessors) {
                start = max(
                    start,
                    earliestFinish.at(predecessor)
                );
            }

            earliestStart[task] = start;
            earliestFinish[task] =
                start + durations.at(task);
        }

        double projectDuration = 0.0;

        for (const auto& [task, finish] : earliestFinish) {
            projectDuration = max(projectDuration, finish);
        }

        for (const string& task : order) {
            cout << left
                 << setw(8) << task
                 << " Start="
                 << setw(6)
                 << fixed
                 << setprecision(1)
                 << earliestStart[task]
                 << " Finish="
                 << setw(6)
                 << earliestFinish[task]
                 << " "
                 << wbs.getNode(task).name
                 << "\n";
        }

        cout << "\nProject duration: "
             << projectDuration
             << " days\n";


        // --------------------------------------------------------------------
        // CRITICAL PATH
        // --------------------------------------------------------------------

        printSection("5. CRITICAL PATH");

        map<string, vector<string>> successors;

        for (const string& task : order) {
            successors[task] = {};
        }

        for (const auto& [task, predecessors] :
             graph.allDependencies()) {

            for (const string& predecessor : predecessors) {
                successors[predecessor].push_back(task);
            }
        }

        map<string, double> latestFinish;
        map<string, double> latestStart;

        for (const string& task : order) {
            latestFinish[task] = projectDuration;
        }

        for (auto iterator = order.rbegin();
             iterator != order.rend();
             ++iterator) {

            const string& task = *iterator;

            if (!successors[task].empty()) {
                double minimumStart =
                    numeric_limits<double>::infinity();

                for (const string& successor :
                     successors[task]) {
                    minimumStart = min(
                        minimumStart,
                        latestStart[successor]
                    );
                }

                latestFinish[task] = minimumStart;
            }

            latestStart[task] =
                latestFinish[task] - durations[task];
        }

        map<string, double> taskFloat;

        for (const string& task : order) {
            taskFloat[task] =
                latestStart[task] -
                earliestStart[task];
        }

        cout << "Critical-path tasks:\n";

        for (const string& task : order) {
            if (fabs(taskFloat[task]) < 1e-9) {
                cout << "  "
                     << task
                     << " | "
                     << wbs.getNode(task).name
                     << " | Duration="
                     << durations[task]
                     << " days\n";
            }
        }


        // --------------------------------------------------------------------
        // WBS DICTIONARY
        // --------------------------------------------------------------------

        printSection("6. WBS DICTIONARY");

        const WBSNode& mfa =
            wbs.getNode("1.3.1.3");

        cout << "Code: "
             << mfa.code
             << "\n";

        cout << "Name: "
             << mfa.name
             << "\n";

        cout << "Type: "
             << mfa.type
             << "\n";

        cout << "Duration: "
             << mfa.durationDays
             << " days\n";

        cout << "Cost: "
             << formatCurrency(mfa.cost)
             << "\n";

        cout <<
            "A WBS dictionary supplies the information needed "
            "to interpret the work package consistently.\n";


        // --------------------------------------------------------------------
        // RESOURCE PLANNING
        // --------------------------------------------------------------------

        printSection("7. RESOURCE PLANNING");

        vector<Resource> resources = {
            {"Asha", "Project Manager", 80, 450},
            {"Ravi", "Backend Engineer", 100, 650},
            {"Meera", "Frontend Engineer", 100, 600},
            {"Kabir", "Security Engineer", 60, 700},
            {"Neha", "QA Engineer", 100, 500}
        };

        for (const Resource& resource : resources) {
            resource.validate();

            cout << left
                 << setw(10) << resource.name
                 << setw(24) << resource.role
                 << "Capacity="
                 << setw(5)
                 << resource.capacityPercent
                 << "% Daily Cost="
                 << formatCurrency(resource.dailyCost)
                 << "\n";
        }


        // --------------------------------------------------------------------
        // RISK ANALYSIS
        // --------------------------------------------------------------------

        printSection("8. RISK ANALYSIS");

        vector<Risk> risks = {
            {
                "Third-party API instability",
                0.25,
                10000,
                1500
            },
            {
                "Security remediation",
                0.20,
                15000,
                2500
            },
            {
                "Performance rework",
                0.30,
                8000,
                1200
            }
        };

        double totalRiskExposure = 0.0;

        for (const Risk& risk : risks) {
            const double emv =
                risk.expectedMonetaryValue();

            totalRiskExposure += emv;

            cout << left
                 << setw(32)
                 << risk.name
                 << "Probability="
                 << risk.probability * 100
                 << "% EMV="
                 << formatCurrency(emv)
                 << "\n";
        }

        cout << "\nTotal expected risk exposure: "
             << formatCurrency(totalRiskExposure)
             << "\n";


        // --------------------------------------------------------------------
        // REQUIREMENT TRACEABILITY
        // --------------------------------------------------------------------

        printSection("9. REQUIREMENT TRACEABILITY");

        map<string, vector<string>> requirements = {
            {
                "REQ-001",
                {"1.3.1.1", "1.3.1.2", "1.3.1.3"}
            },
            {
                "REQ-002",
                {"1.3.2.1", "1.3.2.2"}
            },
            {
                "REQ-003",
                {"1.4.2.1", "1.4.2.2"}
            },
            {
                "REQ-004",
                {"1.5.2.1", "1.5.2.2"}
            }
        };

        for (const auto& [requirement, packages] :
             requirements) {

            cout << requirement << ":\n";

            for (const string& package : packages) {
                cout << "    -> "
                     << package
                     << " "
                     << wbs.getNode(package).name
                     << "\n";
            }
        }


        // --------------------------------------------------------------------
        // CHANGE CONTROL
        // --------------------------------------------------------------------

        printSection("10. CHANGE CONTROL");

        ChangeRequest change {
            "CR-001",
            "Add enterprise single sign-on",
            12000,
            8,
            "New customer requirement",
            "Proposed"
        };

        cout << "ID: "
             << change.id
             << "\n";

        cout << "Description: "
             << change.description
             << "\n";

        cout << "Cost impact: "
             << formatCurrency(change.estimatedCost)
             << "\n";

        cout << "Duration impact: "
             << change.estimatedDurationDays
             << " days\n";

        cout << "Status: "
             << change.status
             << "\n";


        // --------------------------------------------------------------------
        // EARNED VALUE
        // --------------------------------------------------------------------

        printSection("11. EARNED VALUE MANAGEMENT");

        EarnedValue earnedValue {
            50000,
            45000,
            48000
        };

        cout << "PV: "
             << formatCurrency(earnedValue.plannedValue)
             << "\n";

        cout << "EV: "
             << formatCurrency(earnedValue.earnedValue)
             << "\n";

        cout << "AC: "
             << formatCurrency(earnedValue.actualCost)
             << "\n";

        cout << "CV: "
             << formatCurrency(earnedValue.costVariance())
             << "\n";

        cout << "SV: "
             << formatCurrency(earnedValue.scheduleVariance())
             << "\n";

        cout << "CPI: "
             << earnedValue.costPerformanceIndex()
             << "\n";

        cout << "SPI: "
             << earnedValue.schedulePerformanceIndex()
             << "\n";


        // --------------------------------------------------------------------
        // WBS VALIDATION
        // --------------------------------------------------------------------

        printSection("12. WBS VALIDATION");

        int rootCount = 0;
        int errors = 0;

        for (const auto& [code, node] :
             wbs.allNodes()) {

            if (node.parentCode.empty()) {
                ++rootCount;
            }

            if (!node.parentCode.empty() &&
                !wbs.allNodes().count(node.parentCode)) {

                ++errors;

                cout << "ERROR: "
                     << code
                     << " has missing parent.\n";
            }

            if (node.cost < 0) {
                ++errors;

                cout << "ERROR: "
                     << code
                     << " has negative cost.\n";
            }

            if (node.durationDays < 0) {
                ++errors;

                cout << "ERROR: "
                     << code
                     << " has negative duration.\n";
            }

            if (
                node.type == "Work Package" &&
                !node.isLeaf()
            ) {
                ++errors;

                cout << "ERROR: "
                     << code
                     << " is a work package but has children.\n";
            }
        }

        if (rootCount != 1) {
            ++errors;

            cout << "ERROR: Expected one WBS root, found "
                 << rootCount
                 << ".\n";
        }

        if (errors == 0) {
            cout << "WBS validation passed.\n";
        } else {
            cout << "Validation errors: "
                 << errors
                 << "\n";
        }


        // --------------------------------------------------------------------
        // PERFORMANCE AND COMPLEXITY
        // --------------------------------------------------------------------

        printSection("13. ALGORITHMIC COMPLEXITY");

        cout << R"(
WBS tree traversal:
    O(N)

Cost roll-up:
    O(N) for a full traversal.

Dependency topological sorting:
    O(V + E)

Critical-path calculation:
    O(V + E)

N = number of WBS nodes.
V = number of dependency-graph vertices.
E = number of dependency relationships.

The WBS hierarchy and dependency graph solve different problems. The tree
models scope; the directed acyclic graph models precedence.
)";


        // --------------------------------------------------------------------
        // SECURITY
        // --------------------------------------------------------------------

        printSection("14. SECURITY CONSIDERATIONS");

        cout << R"(
Production WBS systems can contain sensitive information such as budgets,
employee assignments, security architecture, vulnerabilities, infrastructure
plans, and customer requirements.

Relevant controls include:
    - authentication,
    - authorization,
    - least privilege,
    - audit logging,
    - input validation,
    - controlled baseline modification,
    - encrypted transport and storage where appropriate,
    - dependency validation,
    - controlled exports.
)";


        // --------------------------------------------------------------------
        // FINAL REPORT
        // --------------------------------------------------------------------

        printSection("15. FINAL PROJECT REPORT");

        cout << "Project: "
             << wbs.getProjectName()
             << "\n";

        cout << "WBS nodes: "
             << wbs.size()
             << "\n";

        cout << "Work packages: "
             << wbs.getLeaves().size()
             << "\n";

        cout << "Total budget: "
             << formatCurrency(totalCost)
             << "\n";

        cout << "Total estimated person-days: "
             << totalEffort
             << "\n";

        cout << "Dependency-aware duration: "
             << projectDuration
             << " days\n";

        cout << "Expected risk exposure: "
             << formatCurrency(totalRiskExposure)
             << "\n";

        cout << R"(
The WBS establishes the scope hierarchy.

The dependency graph establishes precedence.

The schedule transforms dependencies and durations into timing information.

The critical path identifies tasks with no available schedule float.

The cost model aggregates work-package estimates.

The resource model represents capacity and ownership.

The risk model represents uncertainty.

The traceability model connects requirements to implementation scope.

These structures can be integrated into a project-control system while keeping
their individual responsibilities clear.
)";

        return 0;
    }
    catch (const exception& error) {
        cerr << "\nPROGRAM ERROR: "
             << error.what()
             << "\n";

        return 1;
    }
}
