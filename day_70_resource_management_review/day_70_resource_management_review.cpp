/*
 * RESOURCE MANAGEMENT REVIEW
 * Team Management and Resource Allocation Governance Engine
 *
 * Standard: C++17
 *
 * Engineering focus:
 * - Domain-driven resource modeling
 * - Capacity and workload validation
 * - Skill-based resource assignment
 * - Allocation conflict detection
 * - Review policy evaluation
 * - Approval and decision management
 * - Branch-independent governance rules
 * - Risk assessment
 * - Workload fairness
 * - Audit event tracking
 *
 * Compile:
 * g++ -std=c++17 -O2 -Wall -Wextra -pedantic resource_review.cpp -o resource_review
 */

#include <algorithm>
#include <cmath>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;


// ---------------------------------------------------------
// ENUMERATIONS
// ---------------------------------------------------------

enum class EmployeeStatus {
    ACTIVE,
    ON_LEAVE,
    INACTIVE
};

enum class ProjectStatus {
    ACTIVE,
    ON_HOLD,
    COMPLETED
};

enum class ReviewStatus {
    DRAFT,
    UNDER_REVIEW,
    APPROVED,
    REJECTED
};

enum class RiskLevel {
    LOW,
    MEDIUM,
    HIGH,
    CRITICAL
};

enum class ActionStatus {
    OPEN,
    IN_PROGRESS,
    COMPLETED,
    CANCELLED
};

enum class DecisionType {
    APPROVE,
    REJECT
};


// ---------------------------------------------------------
// DOMAIN EXCEPTIONS
// ---------------------------------------------------------

class ResourceException : public runtime_error {
public:
    explicit ResourceException(const string& message)
        : runtime_error(message) {}
};


// ---------------------------------------------------------
// ENUM CONVERSION
// ---------------------------------------------------------

string toString(EmployeeStatus status) {
    switch (status) {
        case EmployeeStatus::ACTIVE: return "ACTIVE";
        case EmployeeStatus::ON_LEAVE: return "ON_LEAVE";
        case EmployeeStatus::INACTIVE: return "INACTIVE";
    }
    return "UNKNOWN";
}

string toString(ProjectStatus status) {
    switch (status) {
        case ProjectStatus::ACTIVE: return "ACTIVE";
        case ProjectStatus::ON_HOLD: return "ON_HOLD";
        case ProjectStatus::COMPLETED: return "COMPLETED";
    }
    return "UNKNOWN";
}

string toString(ReviewStatus status) {
    switch (status) {
        case ReviewStatus::DRAFT: return "DRAFT";
        case ReviewStatus::UNDER_REVIEW: return "UNDER_REVIEW";
        case ReviewStatus::APPROVED: return "APPROVED";
        case ReviewStatus::REJECTED: return "REJECTED";
    }
    return "UNKNOWN";
}

string toString(RiskLevel level) {
    switch (level) {
        case RiskLevel::LOW: return "LOW";
        case RiskLevel::MEDIUM: return "MEDIUM";
        case RiskLevel::HIGH: return "HIGH";
        case RiskLevel::CRITICAL: return "CRITICAL";
    }
    return "UNKNOWN";
}


// ---------------------------------------------------------
// DATE REPRESENTATION
// ---------------------------------------------------------

struct Date {
    int year;
    int month;
    int day;

    bool operator<(const Date& other) const {
        return tie(year, month, day) <
               tie(other.year, other.month, other.day);
    }

    bool operator<=(const Date& other) const {
        return *this < other ||
               (year == other.year &&
                month == other.month &&
                day == other.day);
    }
};

bool validDate(const Date& date) {
    if (date.year < 1900 ||
        date.month < 1 ||
        date.month > 12 ||
        date.day < 1 ||
        date.day > 31) {
        return false;
    }

    static const int days[] = {
        31, 28, 31, 30, 31, 30,
        31, 31, 30, 31, 30, 31
    };

    int maximum = days[date.month - 1];

    bool leap = date.year % 400 == 0 ||
                (date.year % 4 == 0 &&
                 date.year % 100 != 0);

    if (date.month == 2 && leap) {
        maximum = 29;
    }

    return date.day <= maximum;
}

bool overlaps(
    const Date& aStart,
    const Date& aEnd,
    const Date& bStart,
    const Date& bEnd
) {
    return aStart <= bEnd && bStart <= aEnd;
}


// ---------------------------------------------------------
// DATA STRUCTURES
// ---------------------------------------------------------

struct Employee {
    string id;
    string name;
    string department;
    string role;

    map<string, int> skills;

    double weeklyCapacity = 40.0;

    EmployeeStatus status = EmployeeStatus::ACTIVE;
};

struct Project {
    string id;
    string name;

    map<string, int> requiredSkills;

    int priority = 3;

    ProjectStatus status = ProjectStatus::ACTIVE;
};

struct Allocation {
    string id;
    string employeeId;
    string projectId;

    double weeklyHours;

    Date start;
    Date end;
};

struct LeaveRecord {
    string employeeId;
    Date start;
    Date end;
    double unavailableHours;
};

struct CapacityReport {
    string employeeId;
    double grossCapacity;
    double unavailableHours;
    double allocatedHours;
    double availableHours;
    double utilization;
    bool overallocated;
};

struct Risk {
    string employeeId;
    RiskLevel level;
    string reason;
};

struct ReviewAction {
    string id;
    string description;
    string ownerId;
    Date dueDate;
    ActionStatus status = ActionStatus::OPEN;
};

struct Review {
    string id;
    string reviewer;

    Date start;
    Date end;

    ReviewStatus status = ReviewStatus::DRAFT;

    vector<string> findings;
    vector<ReviewAction> actions;

    string decisionNotes;
};

struct AuditEvent {
    string eventType;
    string entityId;
    string description;
};


// ---------------------------------------------------------
// RESOURCE GOVERNANCE ENGINE
// ---------------------------------------------------------

class ResourceGovernanceEngine {

private:

    map<string, Employee> employees;
    map<string, Project> projects;
    map<string, Allocation> allocations;

    vector<LeaveRecord> leaveRecords;
    map<string, Review> reviews;

    vector<AuditEvent> auditLog;

    static void requireText(
        const string& value,
        const string& field
    ) {
        if (value.empty()) {
            throw ResourceException(field + " is required.");
        }
    }

    static void validateSkills(
        const map<string, int>& skills
    ) {
        for (const auto& item : skills) {
            requireText(item.first, "Skill name");

            if (item.second < 1 || item.second > 5) {
                throw ResourceException(
                    "Skill level must be between 1 and 5."
                );
            }
        }
    }

    const Employee& getEmployee(
        const string& id
    ) const {
        auto it = employees.find(id);

        if (it == employees.end()) {
            throw ResourceException("Employee not found: " + id);
        }

        return it->second;
    }

    const Project& getProject(
        const string& id
    ) const {
        auto it = projects.find(id);

        if (it == projects.end()) {
            throw ResourceException("Project not found: " + id);
        }

        return it->second;
    }

    void record(
        const string& event,
        const string& entity,
        const string& description
    ) {
        auditLog.push_back({
            event,
            entity,
            description
        });
    }

    double unavailableHours(
        const string& employeeId,
        const Date& start,
        const Date& end
    ) const {

        double total = 0;

        for (const auto& leave : leaveRecords) {
            if (
                leave.employeeId == employeeId &&
                overlaps(
                    start, end,
                    leave.start, leave.end
                )
            ) {
                total += leave.unavailableHours;
            }
        }

        return min(
            total,
            getEmployee(employeeId).weeklyCapacity
        );
    }

    double allocatedHours(
        const string& employeeId,
        const Date& start,
        const Date& end
    ) const {

        double total = 0;

        for (const auto& entry : allocations) {
            const Allocation& allocation = entry.second;

            if (
                allocation.employeeId == employeeId &&
                overlaps(
                    start, end,
                    allocation.start, allocation.end
                )
            ) {
                total += allocation.weeklyHours;
            }
        }

        return total;
    }

public:

    // -----------------------------------------------------
    // EMPLOYEE MANAGEMENT
    // -----------------------------------------------------

    void addEmployee(const Employee& employee) {

        requireText(employee.id, "Employee ID");
        requireText(employee.name, "Employee name");
        requireText(employee.department, "Department");

        if (employee.weeklyCapacity <= 0 ||
            !isfinite(employee.weeklyCapacity)) {
            throw ResourceException("Invalid weekly capacity.");
        }

        validateSkills(employee.skills);

        if (employees.count(employee.id)) {
            throw ResourceException("Duplicate employee ID.");
        }

        employees.emplace(employee.id, employee);

        record(
            "EMPLOYEE_CREATED",
            employee.id,
            employee.name
        );
    }

    void updateEmployeeStatus(
        const string& employeeId,
        EmployeeStatus status
    ) {
        auto it = employees.find(employeeId);

        if (it == employees.end()) {
            throw ResourceException("Employee not found.");
        }

        it->second.status = status;

        record(
            "EMPLOYEE_STATUS_CHANGED",
            employeeId,
            toString(status)
        );
    }

    // -----------------------------------------------------
    // PROJECT MANAGEMENT
    // -----------------------------------------------------

    void addProject(const Project& project) {

        requireText(project.id, "Project ID");
        requireText(project.name, "Project name");

        if (project.priority < 1 || project.priority > 5) {
            throw ResourceException("Invalid project priority.");
        }

        validateSkills(project.requiredSkills);

        if (projects.count(project.id)) {
            throw ResourceException("Duplicate project ID.");
        }

        projects.emplace(project.id, project);

        record(
            "PROJECT_CREATED",
            project.id,
            project.name
        );
    }

    // -----------------------------------------------------
    // LEAVE MANAGEMENT
    // -----------------------------------------------------

    void addLeave(const LeaveRecord& leave) {

        getEmployee(leave.employeeId);

        if (
            !validDate(leave.start) ||
            !validDate(leave.end) ||
            !(leave.start <= leave.end)
        ) {
            throw ResourceException("Invalid leave period.");
        }

        if (
            leave.unavailableHours < 0 ||
            leave.unavailableHours > 40 ||
            !isfinite(leave.unavailableHours)
        ) {
            throw ResourceException("Invalid unavailable hours.");
        }

        leaveRecords.push_back(leave);

        record(
            "LEAVE_RECORDED",
            leave.employeeId,
            "Unavailable hours recorded."
        );
    }

    // -----------------------------------------------------
    // CAPACITY MANAGEMENT
    // -----------------------------------------------------

    CapacityReport capacity(
        const string& employeeId,
        const Date& start,
        const Date& end
    ) const {

        if (!validDate(start) ||
            !validDate(end) ||
            !(start <= end)) {
            throw ResourceException("Invalid capacity period.");
        }

        const Employee& employee = getEmployee(employeeId);

        if (employee.status != EmployeeStatus::ACTIVE) {
            return {
                employeeId,
                employee.weeklyCapacity,
                employee.weeklyCapacity,
                0,
                0,
                0,
                false
            };
        }

        double unavailable = unavailableHours(
            employeeId, start, end
        );

        double gross = max(
            0.0,
            employee.weeklyCapacity - unavailable
        );

        double allocated = allocatedHours(
            employeeId, start, end
        );

        double available = max(
            0.0,
            gross - allocated
        );

        double utilization = gross > 0
            ? allocated / gross * 100
            : 0;

        return {
            employeeId,
            gross,
            unavailable,
            allocated,
            available,
            utilization,
            allocated > gross
        };
    }

    // -----------------------------------------------------
    // ALLOCATION MANAGEMENT
    // -----------------------------------------------------

    void allocate(const Allocation& allocation) {

        requireText(allocation.id, "Allocation ID");

        const Employee& employee = getEmployee(
            allocation.employeeId
        );

        const Project& project = getProject(
            allocation.projectId
        );

        if (allocations.count(allocation.id)) {
            throw ResourceException("Duplicate allocation ID.");
        }

        if (employee.status != EmployeeStatus::ACTIVE) {
            throw ResourceException("Employee is not active.");
        }

        if (project.status != ProjectStatus::ACTIVE) {
            throw ResourceException("Project is not active.");
        }

        if (
            !validDate(allocation.start) ||
            !validDate(allocation.end) ||
            !(allocation.start <= allocation.end)
        ) {
            throw ResourceException("Invalid allocation dates.");
        }

        if (
            allocation.weeklyHours <= 0 ||
            !isfinite(allocation.weeklyHours)
        ) {
            throw ResourceException("Invalid allocation hours.");
        }

        CapacityReport report = capacity(
            allocation.employeeId,
            allocation.start,
            allocation.end
        );

        if (allocation.weeklyHours > report.availableHours) {
            throw ResourceException(
                "Allocation exceeds available capacity."
            );
        }

        // The allocation is committed only after every
        // validation rule has passed.
        allocations.emplace(allocation.id, allocation);

        record(
            "RESOURCE_ALLOCATED",
            allocation.id,
            allocation.employeeId + " -> " +
            allocation.projectId
        );
    }

    // -----------------------------------------------------
    // RESOURCE REPORTING
    // -----------------------------------------------------

    vector<CapacityReport> utilizationReport(
        const Date& start,
        const Date& end
    ) const {

        vector<CapacityReport> reports;

        for (const auto& item : employees) {
            if (item.second.status != EmployeeStatus::ACTIVE) {
                continue;
            }

            reports.push_back(
                capacity(item.first, start, end)
            );
        }

        return reports;
    }

    // -----------------------------------------------------
    // SKILL MATCHING
    // -----------------------------------------------------

    map<string, double> skillMatching(
        const string& projectId
    ) const {

        const Project& project = getProject(projectId);

        map<string, double> scores;

        for (const auto& item : employees) {

            const Employee& employee = item.second;

            if (employee.status != EmployeeStatus::ACTIVE) {
                continue;
            }

            int matched = 0;
            int required = static_cast<int>(
                project.requiredSkills.size()
            );

            for (const auto& skill : project.requiredSkills) {

                auto employeeSkill = employee.skills.find(
                    skill.first
                );

                if (
                    employeeSkill != employee.skills.end() &&
                    employeeSkill->second >= skill.second
                ) {
                    ++matched;
                }
            }

            scores[employee.id] = required == 0
                ? 100.0
                : static_cast<double>(matched) /
                  required * 100.0;
        }

        return scores;
    }

    // -----------------------------------------------------
    // RISK ASSESSMENT
    // -----------------------------------------------------

    vector<Risk> riskAssessment(
        const Date& start,
        const Date& end
    ) const {

        vector<Risk> risks;

        for (const auto& report : utilizationReport(start, end)) {

            if (report.overallocated) {
                risks.push_back({
                    report.employeeId,
                    RiskLevel::CRITICAL,
                    "Allocated hours exceed available capacity."
                });
            }
            else if (report.utilization >= 95) {
                risks.push_back({
                    report.employeeId,
                    RiskLevel::HIGH,
                    "Very limited capacity buffer."
                });
            }
            else if (report.utilization >= 85 ||
                     report.utilization < 40) {
                risks.push_back({
                    report.employeeId,
                    RiskLevel::MEDIUM,
                    "Workload distribution requires examination."
                });
            }
            else {
                risks.push_back({
                    report.employeeId,
                    RiskLevel::LOW,
                    "Utilization is within the operating range."
                });
            }
        }

        return risks;
    }

    // -----------------------------------------------------
    // FAIRNESS ANALYSIS
    // -----------------------------------------------------

    pair<double, double> fairnessReport(
        const Date& start,
        const Date& end
    ) const {

        auto reports = utilizationReport(start, end);

        if (reports.empty()) {
            return {0, 0};
        }

        vector<double> values;

        for (const auto& report : reports) {
            values.push_back(report.utilization);
        }

        double average = accumulate(
            values.begin(),
            values.end(),
            0.0
        ) / values.size();

        double variance = 0;

        for (double value : values) {
            variance += pow(value - average, 2);
        }

        variance /= values.size();

        return {
            average,
            sqrt(variance)
        };
    }

    // -----------------------------------------------------
    // REVIEW MANAGEMENT
    // -----------------------------------------------------

    Review createReview(
        const string& reviewId,
        const string& reviewer,
        const Date& start,
        const Date& end
    ) {

        requireText(reviewId, "Review ID");
        requireText(reviewer, "Reviewer");

        if (
            !validDate(start) ||
            !validDate(end) ||
            !(start <= end)
        ) {
            throw ResourceException("Invalid review period.");
        }

        if (reviews.count(reviewId)) {
            throw ResourceException("Review already exists.");
        }

        Review review;

        review.id = reviewId;
        review.reviewer = reviewer;
        review.start = start;
        review.end = end;
        review.status = ReviewStatus::UNDER_REVIEW;

        for (const auto& risk : riskAssessment(start, end)) {

            if (
                risk.level == RiskLevel::HIGH ||
                risk.level == RiskLevel::CRITICAL
            ) {
                review.findings.push_back(
                    risk.employeeId + ": " + risk.reason
                );
            }
        }

        reviews.emplace(reviewId, review);

        record(
            "REVIEW_CREATED",
            reviewId,
            reviewer
        );

        return review;
    }

    void addAction(
        const string& reviewId,
        const ReviewAction& action
    ) {

        auto it = reviews.find(reviewId);

        if (it == reviews.end()) {
            throw ResourceException("Review not found.");
        }

        if (it->second.status != ReviewStatus::UNDER_REVIEW) {
            throw ResourceException("Review is not editable.");
        }

        requireText(action.id, "Action ID");
        requireText(action.description, "Action description");

        getEmployee(action.ownerId);

        if (!validDate(action.dueDate)) {
            throw ResourceException("Invalid action due date.");
        }

        auto& actions = it->second.actions;

        auto duplicate = find_if(
            actions.begin(),
            actions.end(),
            [&](const ReviewAction& existing) {
                return existing.id == action.id;
            }
        );

        if (duplicate != actions.end()) {
            throw ResourceException("Duplicate action ID.");
        }

        actions.push_back(action);

        record(
            "ACTION_CREATED",
            action.id,
            reviewId
        );
    }

    void decideReview(
        const string& reviewId,
        DecisionType decision,
        const string& decisionMaker,
        const string& notes
    ) {

        auto it = reviews.find(reviewId);

        if (it == reviews.end()) {
            throw ResourceException("Review not found.");
        }

        Review& review = it->second;

        if (review.status != ReviewStatus::UNDER_REVIEW) {
            throw ResourceException("Review already finalized.");
        }

        requireText(decisionMaker, "Decision maker");
        requireText(notes, "Decision notes");

        bool critical = any_of(
            review.findings.begin(),
            review.findings.end(),
            [](const string& finding) {
                return finding.find("CRITICAL") != string::npos;
            }
        );

        // The decision is not applied when a critical finding
        // exists. A corrective review is required first.
        if (
            decision == DecisionType::APPROVE &&
            critical
        ) {
            throw ResourceException(
                "Critical findings block approval."
            );
        }

        review.status = decision == DecisionType::APPROVE
            ? ReviewStatus::APPROVED
            : ReviewStatus::REJECTED;

        review.decisionNotes = notes;

        record(
            "REVIEW_DECIDED",
            reviewId,
            decisionMaker + ": " + toString(review.status)
        );
    }

    // -----------------------------------------------------
    // AUDIT AND REPORTING
    // -----------------------------------------------------

    void printAuditLog() const {

        cout << "\nAUDIT LOG\n";

        for (const auto& event : auditLog) {
            cout << event.eventType
                 << " | "
                 << event.entityId
                 << " | "
                 << event.description
                 << '\n';
        }
    }

    void printReview(const string& reviewId) const {

        auto it = reviews.find(reviewId);

        if (it == reviews.end()) {
            throw ResourceException("Review not found.");
        }

        const Review& review = it->second;

        cout << "\nRESOURCE REVIEW\n";

        cout << "Review ID: " << review.id << '\n';
        cout << "Reviewer: " << review.reviewer << '\n';

        cout << "Status: "
             << toString(review.status) << '\n';

        cout << "Findings: "
             << review.findings.size() << '\n';

        cout << "Actions: "
             << review.actions.size() << '\n';

        cout << "Decision: "
             << review.decisionNotes << '\n';
    }

    void printEmployeeReport(
        const Date& start,
        const Date& end
    ) const {

        cout << "\nRESOURCE UTILIZATION REPORT\n";

        cout << left
             << setw(12) << "EMPLOYEE"
             << setw(14) << "CAPACITY"
             << setw(14) << "ALLOCATED"
             << setw(14) << "AVAILABLE"
             << setw(14) << "UTILIZATION"
             << '\n';

        for (const auto& report : utilizationReport(start, end)) {

            cout << left
                 << setw(12) << report.employeeId
                 << setw(14) << report.grossCapacity
                 << setw(14) << report.allocatedHours
                 << setw(14) << report.availableHours
                 << fixed << setprecision(2)
                 << report.utilization << "%"
                 << '\n';
        }
    }
};


// ---------------------------------------------------------
// APPLICATION
// ---------------------------------------------------------

int main() {

    try {

        ResourceGovernanceEngine engine;

        const Date start{2026, 11, 1};
        const Date end{2026, 11, 30};

        engine.addEmployee({
            "E101",
            "Aarav Sharma",
            "Engineering",
            "Senior Developer",
            {
                {"python", 5},
                {"sql", 4},
                {"cloud", 4}
            },
            40
        });

        engine.addEmployee({
            "E102",
            "Meera Singh",
            "Engineering",
            "Backend Developer",
            {
                {"python", 4},
                {"sql", 5},
                {"cloud", 3}
            },
            40
        });

        engine.addEmployee({
            "E103",
            "Rohan Verma",
            "Analytics",
            "Data Analyst",
            {
                {"python", 3},
                {"sql", 4},
                {"analytics", 5}
            },
            40
        });

        engine.addEmployee({
            "E104",
            "Ananya Gupta",
            "Engineering",
            "Cloud Engineer",
            {
                {"cloud", 5},
                {"python", 3},
                {"security", 4}
            },
            40
        });

        engine.addProject({
            "P101",
            "Enterprise Platform Modernization",
            {
                {"python", 4},
                {"sql", 4},
                {"cloud", 4}
            },
            5,
            ProjectStatus::ACTIVE
        });

        engine.allocate({
            "A101", "E101", "P101", 35, start, end
        });

        engine.allocate({
            "A102", "E102", "P101", 25, start, end
        });

        engine.allocate({
            "A103", "E103", "P101", 20, start, end
        });

        engine.allocate({
            "A104", "E104", "P101", 30, start, end
        });

        engine.addLeave({
            "E102",
            {2026, 11, 10},
            {2026, 11, 14},
            8
        });

        engine.printEmployeeReport(start, end);

        cout << "\nSKILL MATCHING\n";

        auto scores = engine.skillMatching("P101");

        for (const auto& item : scores) {
            cout << item.first
                 << ": "
                 << fixed << setprecision(2)
                 << item.second
                 << "%\n";
        }

        cout << "\nRISK ASSESSMENT\n";

        for (const auto& risk :
             engine.riskAssessment(start, end)) {

            cout << risk.employeeId
                 << " | "
                 << toString(risk.level)
                 << " | "
                 << risk.reason
                 << '\n';
        }

        auto fairness = engine.fairnessReport(start, end);

        cout << "\nFAIRNESS REPORT\n";
        cout << "Average utilization: "
             << fairness.first << "%\n";

        cout << "Standard deviation: "
             << fairness.second << '\n';

        Review review = engine.createReview(
            "R101",
            "Resource Management Lead",
            start,
            end
        );

        engine.addAction(
            "R101",
            {
                "ACT101",
                "Review engineering capacity distribution",
                "E101",
                {2026, 12, 5},
                ActionStatus::OPEN
            }
        );

        try {

            engine.decideReview(
                "R101",
                DecisionType::APPROVE,
                "Department Head",
                "Resource review approved."
            );

        } catch (const ResourceException& error) {

            cout << "\nAPPROVAL BLOCKED: "
                 << error.what() << '\n';

            engine.decideReview(
                "R101",
                DecisionType::REJECT,
                "Department Head",
                "Critical resource findings require correction."
            );
        }

        engine.printReview("R101");

        engine.printAuditLog();

        // Negative test: capacity violations must fail.
        try {

            engine.allocate({
                "A999",
                "E103",
                "P101",
                50,
                start,
                end
            });

            throw ResourceException(
                "Over-allocation validation failed."
            );

        } catch (const ResourceException& error) {

            cout << "\nCAPACITY VALIDATION: PASSED\n";
            cout << error.what() << '\n';
        }

        cout << "\nRESOURCE MANAGEMENT REVIEW COMPLETED\n";

    } catch (const exception& error) {

        cerr << "APPLICATION ERROR: "
             << error.what()
             << '\n';

        return 1;
    }

    return 0;
}
