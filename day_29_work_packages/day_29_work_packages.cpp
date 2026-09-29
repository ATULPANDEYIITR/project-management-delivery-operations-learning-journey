/*
 * Work Packages: Understanding Manageable Units of Work
 *
 * C++17 industry-style case study.
 *
 * Scenario:
 * A software company is delivering a production web application. The project
 * is decomposed into work packages so that effort, ownership, dependencies,
 * risks, progress, cost, and quality can be managed systematically.
 *
 * The program demonstrates:
 * - work-package modeling
 * - deliverables and acceptance criteria
 * - validation
 * - dependency graphs
 * - topological sorting
 * - critical-path analysis
 * - three-point estimation
 * - resource capacity
 * - risk exposure
 * - change control
 * - progress and earned-value metrics
 * - edge-case handling
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic work_packages.cpp -o work_packages
 *
 * Run:
 *   ./work_packages
 */

#include <algorithm>
#include <cmath>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;

// ============================================================================
// 1. ENUMERATIONS
// ============================================================================

enum class WorkStatus {
    NotStarted,
    InProgress,
    Blocked,
    Complete
};

enum class Priority {
    Low,
    Medium,
    High,
    Critical
};

string toString(WorkStatus status) {
    switch (status) {
        case WorkStatus::NotStarted:
            return "Not Started";
        case WorkStatus::InProgress:
            return "In Progress";
        case WorkStatus::Blocked:
            return "Blocked";
        case WorkStatus::Complete:
            return "Complete";
    }

    return "Unknown";
}

string toString(Priority priority) {
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


// ============================================================================
// 2. DELIVERABLE
// ============================================================================

struct Deliverable {
    string name;
    vector<string> acceptanceCriteria;

    bool isWellDefined() const {
        return !name.empty() && !acceptanceCriteria.empty();
    }
};


// ============================================================================
// 3. WORK PACKAGE
// ============================================================================

class WorkPackage {
private:
    string id_;
    string name_;
    string description_;
    string owner_;
    double estimatedHours_;
    Priority priority_;
    WorkStatus status_;
    set<string> dependencies_;
    vector<Deliverable> deliverables_;
    vector<string> risks_;
    double actualHours_;
    double progressPercent_;

public:
    WorkPackage(
        string id,
        string name,
        string description,
        string owner,
        double estimatedHours,
        Priority priority,
        set<string> dependencies = {},
        vector<Deliverable> deliverables = {},
        vector<string> risks = {}
    )
        : id_(move(id)),
          name_(move(name)),
          description_(move(description)),
          owner_(move(owner)),
          estimatedHours_(estimatedHours),
          priority_(priority),
          status_(WorkStatus::NotStarted),
          dependencies_(move(dependencies)),
          deliverables_(move(deliverables)),
          risks_(move(risks)),
          actualHours_(0.0),
          progressPercent_(0.0) {
        validate();
    }

    const string& id() const {
        return id_;
    }

    const string& name() const {
        return name_;
    }

    const string& owner() const {
        return owner_;
    }

    double estimatedHours() const {
        return estimatedHours_;
    }

    double actualHours() const {
        return actualHours_;
    }

    double progressPercent() const {
        return progressPercent_;
    }

    Priority priority() const {
        return priority_;
    }

    WorkStatus status() const {
        return status_;
    }

    const set<string>& dependencies() const {
        return dependencies_;
    }

    void validate() const {
        if (id_.empty()) {
            throw invalid_argument("Work package ID is required.");
        }

        if (name_.empty()) {
            throw invalid_argument("Work package name is required.");
        }

        if (owner_.empty()) {
            throw invalid_argument("Work package owner is required.");
        }

        if (!isfinite(estimatedHours_) || estimatedHours_ <= 0) {
            throw invalid_argument(
                "Estimated hours must be greater than zero."
            );
        }

        if (progressPercent_ < 0 || progressPercent_ > 100) {
            throw invalid_argument(
                "Progress must be between 0 and 100."
            );
        }

        for (const auto& deliverable : deliverables_) {
            if (!deliverable.isWellDefined()) {
                throw invalid_argument(
                    "Deliverable has incomplete acceptance criteria."
                );
            }
        }
    }

    void updateProgress(double progress, double actualHours) {
        if (progress < 0 || progress > 100) {
            throw invalid_argument(
                "Progress must be between 0 and 100."
            );
        }

        if (actualHours < 0) {
            throw invalid_argument(
                "Actual hours cannot be negative."
            );
        }

        progressPercent_ = progress;
        actualHours_ = actualHours;

        if (progress == 100) {
            status_ = WorkStatus::Complete;
        } else if (progress > 0) {
            status_ = WorkStatus::InProgress;
        } else {
            status_ = WorkStatus::NotStarted;
        }
    }

    void addApprovedHours(double additionalHours) {
        if (additionalHours < 0) {
            throw invalid_argument(
                "Additional hours cannot be negative."
            );
        }

        estimatedHours_ += additionalHours;
    }

    double variance() const {
        return actualHours_ - estimatedHours_;
    }

    int durationDays(double hoursPerDay = 8.0) const {
        if (hoursPerDay <= 0) {
            throw invalid_argument(
                "Hours per day must be positive."
            );
        }

        return max(
            1,
            static_cast<int>(
                ceil(estimatedHours_ / hoursPerDay)
            )
        );
    }
};


// ============================================================================
// 4. PROJECT CONTAINER
// ============================================================================

class ProjectPlan {
private:
    map<string, WorkPackage> packages_;

public:
    void addPackage(WorkPackage package) {
        const string packageId = package.id();

        if (packages_.find(packageId) != packages_.end()) {
            throw invalid_argument(
                "Duplicate work package ID: " + packageId
            );
        }

        packages_.emplace(packageId, move(package));
    }

    const map<string, WorkPackage>& packages() const {
        return packages_;
    }

    map<string, WorkPackage>& packages() {
        return packages_;
    }

    vector<string> validateDependencyReferences() const {
        vector<string> errors;

        for (const auto& [id, package] : packages_) {
            for (const auto& dependency : package.dependencies()) {
                if (packages_.find(dependency) == packages_.end()) {
                    errors.push_back(
                        id + " references unknown dependency " + dependency
                    );
                }
            }
        }

        return errors;
    }

    vector<string> topologicalOrder() const {
        vector<string> errors = validateDependencyReferences();

        if (!errors.empty()) {
            throw runtime_error(errors.front());
        }

        map<string, int> indegree;
        map<string, set<string>> successors;

        for (const auto& [id, package] : packages_) {
            indegree[id] = 0;
            successors[id] = {};
        }

        for (const auto& [id, package] : packages_) {
            for (const auto& dependency : package.dependencies()) {
                successors[dependency].insert(id);
                ++indegree[id];
            }
        }

        // std::priority_queue provides deterministic lexical selection here.
        priority_queue<
            string,
            vector<string>,
            greater<string>
        > ready;

        for (const auto& [id, degree] : indegree) {
            if (degree == 0) {
                ready.push(id);
            }
        }

        vector<string> order;

        while (!ready.empty()) {
            const string current = ready.top();
            ready.pop();

            order.push_back(current);

            for (const auto& successor : successors[current]) {
                --indegree[successor];

                if (indegree[successor] == 0) {
                    ready.push(successor);
                }
            }
        }

        if (order.size() != packages_.size()) {
            throw runtime_error(
                "Dependency cycle detected."
            );
        }

        return order;
    }

    pair<double, vector<string>> longestDependencyPath() const {
        const vector<string> order = topologicalOrder();

        map<string, double> earliestFinish;
        map<string, string> predecessor;

        for (const auto& id : order) {
            const WorkPackage& package = packages_.at(id);

            double bestFinish = 0.0;
            string bestPredecessor;

            for (const auto& dependency : package.dependencies()) {
                const double candidate = earliestFinish.at(dependency);

                if (candidate > bestFinish) {
                    bestFinish = candidate;
                    bestPredecessor = dependency;
                }
            }

            earliestFinish[id] =
                bestFinish + package.estimatedHours();

            predecessor[id] = bestPredecessor;
        }

        string finalPackage;
        double maximumFinish = -numeric_limits<double>::infinity();

        for (const auto& [id, finish] : earliestFinish) {
            if (finish > maximumFinish) {
                maximumFinish = finish;
                finalPackage = id;
            }
        }

        vector<string> path;
        string current = finalPackage;

        while (!current.empty()) {
            path.push_back(current);
            current = predecessor[current];
        }

        reverse(path.begin(), path.end());

        return {maximumFinish, path};
    }
};


// ============================================================================
// 5. THREE-POINT ESTIMATION
// ============================================================================

class ThreePointEstimate {
private:
    double optimistic_;
    double mostLikely_;
    double pessimistic_;

public:
    ThreePointEstimate(
        double optimistic,
        double mostLikely,
        double pessimistic
    )
        : optimistic_(optimistic),
          mostLikely_(mostLikely),
          pessimistic_(pessimistic) {
        validate();
    }

    void validate() const {
        if (
            optimistic_ < 0 ||
            mostLikely_ < 0 ||
            pessimistic_ < 0
        ) {
            throw invalid_argument(
                "Estimates cannot be negative."
            );
        }

        if (!(
            optimistic_ <=
            mostLikely_ &&
            mostLikely_ <=
            pessimistic_
        )) {
            throw invalid_argument(
                "Expected optimistic <= most likely <= pessimistic."
            );
        }
    }

    double pert() const {
        return (
            optimistic_ +
            4.0 * mostLikely_ +
            pessimistic_
        ) / 6.0;
    }
};


// ============================================================================
// 6. RISK
// ============================================================================

struct Risk {
    string id;
    string description;
    double probability;
    double impact;
    string mitigation;

    double expectedExposure() const {
        if (probability < 0 || probability > 1) {
            throw invalid_argument(
                "Risk probability must be between 0 and 1."
            );
        }

        if (impact < 0) {
            throw invalid_argument(
                "Risk impact cannot be negative."
            );
        }

        return probability * impact;
    }
};


// ============================================================================
// 7. RESOURCE CAPACITY
// ============================================================================

map<string, double> resourceLoad(
    const ProjectPlan& plan
) {
    map<string, double> load;

    for (const auto& [id, package] : plan.packages()) {
        load[package.owner()] += package.estimatedHours();
    }

    return load;
}

map<string, double> detectOverAllocation(
    const ProjectPlan& plan,
    const map<string, double>& capacity
) {
    const auto load = resourceLoad(plan);
    map<string, double> overload;

    for (const auto& [owner, hours] : load) {
        auto found = capacity.find(owner);

        const double available =
            found == capacity.end()
                ? 0.0
                : found->second;

        if (hours > available) {
            overload[owner] = hours - available;
        }
    }

    return overload;
}


// ============================================================================
// 8. CHANGE CONTROL
// ============================================================================

struct ChangeRequest {
    string id;
    string description;
    double addedHours;
    string reason;
    bool approved;

    void validate() const {
        if (description.empty()) {
            throw invalid_argument(
                "Change description is required."
            );
        }

        if (addedHours < 0) {
            throw invalid_argument(
                "Added hours cannot be negative."
            );
        }
    }
};

void applyChange(
    WorkPackage& package,
    const ChangeRequest& change
) {
    change.validate();

    if (!change.approved) {
        throw runtime_error(
            "Unapproved change cannot modify the baseline."
        );
    }

    package.addApprovedHours(change.addedHours);
}


// ============================================================================
// 9. EARNED VALUE
// ============================================================================

struct EarnedValueMetrics {
    double plannedValue;
    double earnedValue;
    double actualCost;
    double cpi;
    double spi;
};

EarnedValueMetrics calculateEVM(
    double plannedValue,
    double earnedValue,
    double actualCost
) {
    if (
        plannedValue < 0 ||
        earnedValue < 0 ||
        actualCost < 0
    ) {
        throw invalid_argument(
            "EVM values cannot be negative."
        );
    }

    const double cpi =
        actualCost == 0
            ? numeric_limits<double>::infinity()
            : earnedValue / actualCost;

    const double spi =
        plannedValue == 0
            ? numeric_limits<double>::infinity()
            : earnedValue / plannedValue;

    return {
        plannedValue,
        earnedValue,
        actualCost,
        cpi,
        spi
    };
}


// ============================================================================
// 10. WEIGHTED PROJECT PROGRESS
// ============================================================================

double weightedProgress(const ProjectPlan& plan) {
    double totalEstimate = 0.0;
    double weightedProgressValue = 0.0;

    for (const auto& [id, package] : plan.packages()) {
        totalEstimate += package.estimatedHours();

        weightedProgressValue +=
            package.estimatedHours() *
            package.progressPercent();
    }

    if (totalEstimate == 0.0) {
        return 0.0;
    }

    return weightedProgressValue / totalEstimate;
}


// ============================================================================
// 11. SIMPLE BUSINESS-DAY SCHEDULER
// ============================================================================

struct Date {
    int year;
    int month;
    int day;
};

Date addCalendarDays(Date date, int days) {
    // This intentionally uses a compact Gregorian calendar calculation.
    // Production scheduling systems should normally use a date library that
    // handles holidays, calendars, time zones, and locale rules explicitly.
    auto isLeapYear = [](int year) {
        return (year % 400 == 0) ||
               (year % 4 == 0 && year % 100 != 0);
    };

    const int daysInMonth[] = {
        31,
        28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31
    };

    while (days > 0) {
        ++date.day;

        int maximumDay = daysInMonth[date.month - 1];

        if (date.month == 2 && isLeapYear(date.year)) {
            maximumDay = 29;
        }

        if (date.day > maximumDay) {
            date.day = 1;
            ++date.month;

            if (date.month > 12) {
                date.month = 1;
                ++date.year;
            }
        }

        --days;
    }

    return date;
}

string dateToString(Date date) {
    ostringstream output;
    output << setfill('0')
           << setw(4) << date.year << "-"
           << setw(2) << date.month << "-"
           << setw(2) << date.day;

    return output.str();
}


// ============================================================================
// 12. DAY-OF-WEEK CALCULATION
// ============================================================================

int dayOfWeek(Date date) {
    // Sakamoto's algorithm:
    // 0 = Sunday, 1 = Monday, ..., 6 = Saturday.
    static const int monthOffsets[] = {
        0, 3, 2, 5, 0, 3,
        5, 1, 4, 6, 2, 4
    };

    int year = date.year;

    if (date.month < 3) {
        --year;
    }

    return (
        year +
        year / 4 -
        year / 100 +
        year / 400 +
        monthOffsets[date.month - 1] +
        date.day
    ) % 7;
}

Date addWorkingDays(Date date, int duration) {
    int remaining = max(0, duration - 1);

    while (remaining > 0) {
        date = addCalendarDays(date, 1);

        const int weekday = dayOfWeek(date);

        if (weekday != 0 && weekday != 6) {
            --remaining;
        }
    }

    return date;
}


// ============================================================================
// 13. SCHEDULE RECORD
// ============================================================================

struct ScheduleEntry {
    Date start;
    Date finish;
};

map<string, ScheduleEntry> createSchedule(
    const ProjectPlan& plan,
    Date projectStart
) {
    const vector<string> order = plan.topologicalOrder();

    map<string, ScheduleEntry> schedule;

    for (const auto& id : order) {
        const WorkPackage& package = plan.packages().at(id);

        Date start = projectStart;

        for (const auto& dependency : package.dependencies()) {
            const auto dependencyEntry = schedule.at(dependency);

            Date candidate =
                addCalendarDays(dependencyEntry.finish, 1);

            if (
                dayOfWeek(candidate) == 0
            ) {
                candidate = addCalendarDays(candidate, 1);
            } else if (
                dayOfWeek(candidate) == 6
            ) {
                candidate = addCalendarDays(candidate, 2);
            }

            // Lexicographic date comparison is safe for these integer fields
            // only when converted consistently.
            if (
                dateToString(candidate) >
                dateToString(start)
            ) {
                start = candidate;
            }
        }

        const Date finish =
            addWorkingDays(start, package.durationDays());

        schedule[id] = {start, finish};
    }

    return schedule;
}


// ============================================================================
// 14. BUILD THE CASE STUDY
// ============================================================================

ProjectPlan buildProject() {
    ProjectPlan plan;

    plan.addPackage(
        WorkPackage(
            "WP-101",
            "Requirements Analysis",
            "Define functional and non-functional requirements.",
            "Business Analyst",
            24,
            Priority::Critical,
            {},
            {
                {
                    "Requirements Baseline",
                    {
                        "Business approval exists",
                        "Requirements traceability exists"
                    }
                }
            }
        )
    );

    plan.addPackage(
        WorkPackage(
            "WP-102",
            "UX Design",
            "Design user journeys and interface specifications.",
            "UX Lead",
            32,
            Priority::High,
            {"WP-101"},
            {
                {
                    "UX Specification",
                    {
                        "User journeys approved",
                        "Accessibility requirements documented"
                    }
                }
            }
        )
    );

    plan.addPackage(
        WorkPackage(
            "WP-103",
            "Backend API",
            "Implement authentication and product APIs.",
            "Backend Engineer",
            64,
            Priority::Critical,
            {"WP-101"},
            {
                {
                    "API Service",
                    {
                        "Authentication works",
                        "API tests pass"
                    }
                }
            }
        )
    );

    plan.addPackage(
        WorkPackage(
            "WP-104",
            "Frontend Implementation",
            "Implement the approved interface.",
            "Frontend Engineer",
            56,
            Priority::High,
            {"WP-102", "WP-103"},
            {
                {
                    "Web Application",
                    {
                        "Core journeys work",
                        "Responsive layouts pass testing"
                    }
                }
            }
        )
    );

    plan.addPackage(
        WorkPackage(
            "WP-105",
            "Integration Testing",
            "Validate integrated application behavior.",
            "QA Engineer",
            40,
            Priority::High,
            {"WP-104"},
            {
                {
                    "Integration Test Report",
                    {
                        "Critical scenarios pass",
                        "Defects are dispositioned"
                    }
                }
            }
        )
    );

    plan.addPackage(
        WorkPackage(
            "WP-106",
            "Production Deployment",
            "Deploy the approved application.",
            "DevOps Engineer",
            16,
            Priority::Critical,
            {"WP-105"},
            {
                {
                    "Production Release",
                    {
                        "Health checks pass",
                        "Rollback procedure is verified"
                    }
                }
            }
        )
    );

    return plan;
}


// ============================================================================
// 15. ASSERTION-STYLE TESTS
// ============================================================================

void runTests() {
    ProjectPlan plan = buildProject();

    if (plan.packages().size() != 6) {
        throw runtime_error("Unexpected package count.");
    }

    if (!plan.validateDependencyReferences().empty()) {
        throw runtime_error("Dependency validation failed.");
    }

    const vector<string> order = plan.topologicalOrder();

    if (order.size() != 6) {
        throw runtime_error("Topological ordering failed.");
    }

    try {
        plan.packages().at("WP-101").updateProgress(101, 1);
        throw runtime_error(
            "Invalid progress was not rejected."
        );
    } catch (const invalid_argument&) {
        // Expected behavior.
    }

    try {
        ProjectPlan cyclic;

        cyclic.addPackage(
            WorkPackage(
                "A",
                "A",
                "Cycle A",
                "Owner",
                1,
                Priority::Low,
                {"B"}
            )
        );

        cyclic.addPackage(
            WorkPackage(
                "B",
                "B",
                "Cycle B",
                "Owner",
                1,
                Priority::Low,
                {"A"}
            )
        );

        cyclic.topologicalOrder();

        throw runtime_error(
            "Dependency cycle was not rejected."
        );
    } catch (const runtime_error&) {
        // Expected behavior.
    }

    cout << "\nValidation tests passed.\n";
}


// ============================================================================
// 16. MAIN INDUSTRY CASE STUDY
// ============================================================================

int main() {
    try {
        cout << string(72, '=') << '\n';
        cout << "WORK PACKAGES: MANAGEABLE UNITS OF WORK\n";
        cout << string(72, '=') << "\n\n";

        ProjectPlan plan = buildProject();

        cout << "PACKAGE REGISTER\n";
        cout << left
             << setw(9) << "ID"
             << setw(28) << "Package"
             << setw(22) << "Owner"
             << setw(10) << "Hours"
             << "Priority\n";

        cout << string(80, '-') << '\n';

        for (const auto& [id, package] : plan.packages()) {
            cout << left
                 << setw(9) << id
                 << setw(28) << package.name()
                 << setw(22) << package.owner()
                 << setw(10) << package.estimatedHours()
                 << toString(package.priority())
                 << '\n';
        }

        cout << "\nDEPENDENCY ORDER\n";

        const vector<string> order = plan.topologicalOrder();

        for (size_t i = 0; i < order.size(); ++i) {
            if (i > 0) {
                cout << " -> ";
            }

            cout << order[i];
        }

        cout << '\n';

        cout << "\nCRITICAL-PATH ANALYSIS\n";

        const auto [criticalHours, criticalPath] =
            plan.longestDependencyPath();

        cout << "Longest dependency path: ";

        for (size_t i = 0; i < criticalPath.size(); ++i) {
            if (i > 0) {
                cout << " -> ";
            }

            cout << criticalPath[i];
        }

        cout << "\nPath effort: "
             << fixed
             << setprecision(2)
             << criticalHours
             << " hours\n";

        cout << "\nTHREE-POINT ESTIMATION\n";

        ThreePointEstimate estimate(
            24,
            32,
            56
        );

        cout << "PERT estimate: "
             << fixed
             << setprecision(2)
             << estimate.pert()
             << " hours\n";

        cout << "Cost at $75/hour: $"
             << fixed
             << setprecision(2)
             << estimate.pert() * 75.0
             << '\n';

        cout << "\nRESOURCE CAPACITY\n";

        const map<string, double> capacity = {
            {"Business Analyst", 40},
            {"UX Lead", 40},
            {"Backend Engineer", 80},
            {"Frontend Engineer", 40},
            {"QA Engineer", 40},
            {"DevOps Engineer", 20}
        };

        const auto overload =
            detectOverAllocation(plan, capacity);

        if (overload.empty()) {
            cout << "No overload detected.\n";
        } else {
            for (const auto& [owner, hours] : overload) {
                cout << owner
                     << " overloaded by "
                     << hours
                     << " hours\n";
            }
        }

        cout << "\nRISK ANALYSIS\n";

        const vector<Risk> risks = {
            {
                "R-01",
                "API integration delay",
                0.35,
                20,
                "Prototype high-risk interfaces early."
            },
            {
                "R-02",
                "Late requirements change",
                0.20,
                30,
                "Baseline requirements and control changes."
            }
        };

        for (const auto& risk : risks) {
            cout << risk.id
                 << ": exposure="
                 << fixed
                 << setprecision(2)
                 << risk.expectedExposure()
                 << '\n';
        }

        cout << "\nSCHEDULE\n";

        const map<string, ScheduleEntry> schedule =
            createSchedule(
                plan,
                {2026, 10, 1}
            );

        for (const auto& id : order) {
            const auto& entry = schedule.at(id);

            cout << id
                 << ": "
                 << dateToString(entry.start)
                 << " -> "
                 << dateToString(entry.finish)
                 << '\n';
        }

        cout << "\nPROGRESS TRACKING\n";

        const map<string, pair<double, double>> updates = {
            {"WP-101", {100, 25}},
            {"WP-102", {75, 25}},
            {"WP-103", {60, 42}},
            {"WP-104", {20, 10}},
            {"WP-105", {0, 0}},
            {"WP-106", {0, 0}}
        };

        for (auto& [id, package] : plan.packages()) {
            const auto& [progress, actual] = updates.at(id);

            package.updateProgress(
                progress,
                actual
            );
        }

        for (const auto& [id, package] : plan.packages()) {
            cout << id
                 << ": "
                 << package.progressPercent()
                 << "% | actual="
                 << package.actualHours()
                 << "h | variance="
                 << package.variance()
                 << "h | "
                 << toString(package.status())
                 << '\n';
        }

        cout << "Weighted project progress: "
             << fixed
             << setprecision(2)
             << weightedProgress(plan)
             << "%\n";

        cout << "\nEARNED VALUE MANAGEMENT\n";

        const EarnedValueMetrics evm =
            calculateEVM(
                100000,
                72000,
                80000
            );

        cout << "PV: $" << evm.plannedValue << '\n';
        cout << "EV: $" << evm.earnedValue << '\n';
        cout << "AC: $" << evm.actualCost << '\n';
        cout << "CPI: " << evm.cpi << '\n';
        cout << "SPI: " << evm.spi << '\n';

        cout << "\nCHANGE CONTROL\n";

        ChangeRequest change{
            "CR-001",
            "Add audit logging",
            12,
            "New compliance requirement",
            true
        };

        applyChange(
            plan.packages().at("WP-103"),
            change
        );

        cout << "WP-103 revised estimate: "
             << plan.packages().at("WP-103").estimatedHours()
             << " hours\n";

        cout << "\nEDGE-CASE TESTING\n";

        try {
            ChangeRequest rejectedChange{
                "CR-002",
                "Unapproved feature",
                20,
                "Uncontrolled request",
                false
            };

            applyChange(
                plan.packages().at("WP-103"),
                rejectedChange
            );
        } catch (const exception& error) {
            cout << "Unapproved change rejected: "
                 << error.what()
                 << '\n';
        }

        runTests();

        cout << "\nCASE STUDY COMPLETE\n";
    }
    catch (const exception& error) {
        cerr << "Fatal error: "
             << error.what()
             << '\n';

        return 1;
    }

    return 0;
}
