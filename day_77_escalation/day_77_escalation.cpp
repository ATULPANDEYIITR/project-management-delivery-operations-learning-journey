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
#include <vector>

using namespace std;

enum class Severity {
    LOW = 1,
    MEDIUM = 2,
    HIGH = 3,
    CRITICAL = 4
};

enum class Status {
    REPORTED,
    ACKNOWLEDGED,
    INVESTIGATING,
    ESCALATED,
    RESOLVED,
    CLOSED
};

enum class EscalationLevel {
    L1 = 1,
    L2 = 2,
    L3 = 3,
    EXECUTIVE = 4
};

string toString(Severity severity) {
    switch (severity) {
        case Severity::LOW: return "LOW";
        case Severity::MEDIUM: return "MEDIUM";
        case Severity::HIGH: return "HIGH";
        case Severity::CRITICAL: return "CRITICAL";
    }
    throw runtime_error("Invalid severity.");
}

string toString(Status status) {
    switch (status) {
        case Status::REPORTED: return "REPORTED";
        case Status::ACKNOWLEDGED: return "ACKNOWLEDGED";
        case Status::INVESTIGATING: return "INVESTIGATING";
        case Status::ESCALATED: return "ESCALATED";
        case Status::RESOLVED: return "RESOLVED";
        case Status::CLOSED: return "CLOSED";
    }
    throw runtime_error("Invalid status.");
}

string toString(EscalationLevel level) {
    switch (level) {
        case EscalationLevel::L1: return "LEVEL_1";
        case EscalationLevel::L2: return "LEVEL_2";
        case EscalationLevel::L3: return "LEVEL_3";
        case EscalationLevel::EXECUTIVE: return "EXECUTIVE";
    }
    throw runtime_error("Invalid escalation level.");
}

struct Policy {
    int acknowledgementMinutes;
    int resolutionMinutes;
    EscalationLevel initialLevel;
};

const map<Severity, Policy> POLICIES = {
    {Severity::LOW, {480, 2880, EscalationLevel::L1}},
    {Severity::MEDIUM, {120, 1440, EscalationLevel::L1}},
    {Severity::HIGH, {30, 240, EscalationLevel::L2}},
    {Severity::CRITICAL, {10, 60, EscalationLevel::EXECUTIVE}}
};

struct Actor {
    string id;
    string name;
    string role;
    string department;
};

struct AuditEvent {
    string actorId;
    string action;
    string details;
    chrono::system_clock::time_point timestamp;
};

struct StatusCheck {
    string name;
    bool required;
    bool passed;
    bool completed;
};

struct Incident {
    string id;
    string title;
    string description;
    string category;
    string department;
    string reporterId;
    string assignedTo;

    Severity severity;
    Status status;
    EscalationLevel escalationLevel;

    chrono::system_clock::time_point reportedAt;
    chrono::system_clock::time_point acknowledgementDeadline;
    chrono::system_clock::time_point resolutionDeadline;

    bool acknowledged = false;
    bool resolved = false;
    string resolutionNotes;
    string parentIncidentId;

    vector<AuditEvent> audit;
    vector<StatusCheck> checks;
    set<string> tags;
};

struct GovernancePolicy {
    int requiredApprovals = 2;
    bool requireStatusChecks = true;
    bool requireResolvedIncident = true;
    bool requireAssignedOwner = true;
    bool requireResolutionEvidence = true;
};

class GovernanceEngine {
private:
    unordered_map<string, Actor> actors;
    unordered_map<string, Incident> incidents;
    vector<string> notificationLog;
    int nextIncidentId = 1;

    static string timestamp() {
        auto now = chrono::system_clock::now();
        time_t value = chrono::system_clock::to_time_t(now);

        tm timeInfo{};

#ifdef _WIN32
        localtime_s(&timeInfo, &value);
#else
        localtime_r(&value, &timeInfo);
#endif

        ostringstream output;
        output << put_time(&timeInfo, "%Y-%m-%d %H:%M:%S");
        return output.str();
    }

    Actor& requireActor(const string& actorId) {
        auto it = actors.find(actorId);

        if (it == actors.end()) {
            throw runtime_error("Actor does not exist.");
        }

        return it->second;
    }

    Incident& requireIncident(const string& incidentId) {
        auto it = incidents.find(incidentId);

        if (it == incidents.end()) {
            throw runtime_error("Incident does not exist.");
        }

        return it->second;
    }

    static void validateText(
        const string& value,
        const string& field,
        size_t maximum
    ) {
        if (value.empty() || value.size() > maximum) {
            throw invalid_argument(field + " is invalid.");
        }

        if (value.find('\0') != string::npos) {
            throw invalid_argument(field + " contains invalid data.");
        }
    }

    static bool canManage(const Actor& actor, Severity severity) {
        if (
            actor.role == "administrator" ||
            actor.role == "incident_manager"
        ) {
            return true;
        }

        if (actor.role == "team_lead") {
            return severity != Severity::CRITICAL;
        }

        return actor.role == "responder";
    }

    void authorize(const string& actorId, Severity severity) {
        Actor& actor = requireActor(actorId);

        if (!canManage(actor, severity)) {
            throw runtime_error("Operation not authorized.");
        }
    }

    void audit(
        Incident& incident,
        const string& actorId,
        const string& action,
        const string& details
    ) {
        incident.audit.push_back({
            actorId,
            action,
            details,
            chrono::system_clock::now()
        });
    }

    void notify(
        const Incident& incident,
        const string& event,
        const string& recipient
    ) {
        ostringstream message;
        message << event
                << " | " << incident.id
                << " | " << recipient;

        notificationLog.push_back(message.str());
    }

    void transition(
        Incident& incident,
        const string& actorId,
        Status next,
        const string& details
    ) {
        static const map<Status, set<Status>> allowed = {
            {Status::REPORTED, {
                Status::ACKNOWLEDGED, Status::ESCALATED
            }},
            {Status::ACKNOWLEDGED, {
                Status::INVESTIGATING, Status::ESCALATED
            }},
            {Status::INVESTIGATING, {
                Status::ESCALATED, Status::RESOLVED
            }},
            {Status::ESCALATED, {
                Status::ACKNOWLEDGED,
                Status::INVESTIGATING,
                Status::RESOLVED
            }},
            {Status::RESOLVED, {
                Status::CLOSED, Status::INVESTIGATING
            }},
            {Status::CLOSED, {}}
        };

        if (!allowed.at(incident.status).count(next)) {
            throw runtime_error("Invalid incident state transition.");
        }

        Status previous = incident.status;
        incident.status = next;

        audit(
            incident,
            actorId,
            "STATUS_CHANGED",
            toString(previous) + " -> " + toString(next) + ": " + details
        );
    }

public:
    void registerActor(const Actor& actor) {
        validateText(actor.id, "Actor ID", 80);
        validateText(actor.name, "Actor name", 120);
        validateText(actor.department, "Department", 100);

        static const set<string> roles = {
            "reporter",
            "responder",
            "team_lead",
            "incident_manager",
            "administrator"
        };

        if (!roles.count(actor.role)) {
            throw invalid_argument("Invalid actor role.");
        }

        if (actors.count(actor.id)) {
            throw runtime_error("Actor already exists.");
        }

        actors.emplace(actor.id, actor);
    }

    string report(
        const string& reporterId,
        const string& title,
        const string& description,
        const string& category,
        const string& department,
        Severity severity,
        const set<string>& tags = {},
        const string& parentIncidentId = ""
    ) {
        Actor& reporter = requireActor(reporterId);

        validateText(title, "Title", 160);
        validateText(description, "Description", 5000);
        validateText(category, "Category", 80);
        validateText(department, "Department", 100);

        for (const string& tag : tags) {
            validateText(tag, "Tag", 60);
        }

        if (parentIncidentId.size()) {
            requireIncident(parentIncidentId);
        }

        const Policy& policy = POLICIES.at(severity);
        auto now = chrono::system_clock::now();

        ostringstream id;
        id << "INC-" << setw(5) << setfill('0') << nextIncidentId++;

        Incident incident;
        incident.id = id.str();
        incident.title = title;
        incident.description = description;
        incident.category = category;
        incident.department = department;
        incident.reporterId = reporter.id;
        incident.severity = severity;
        incident.status = Status::REPORTED;
        incident.escalationLevel = policy.initialLevel;
        incident.reportedAt = now;
        incident.acknowledgementDeadline =
            now + chrono::minutes(policy.acknowledgementMinutes);
        incident.resolutionDeadline =
            now + chrono::minutes(policy.resolutionMinutes);
        incident.tags = tags;
        incident.parentIncidentId = parentIncidentId;

        incident.audit.push_back({
            reporterId,
            "REPORTED",
            "Incident created",
            now
        });

        incidents.emplace(incident.id, move(incident));

        Incident& stored = incidents.at(id.str());

        notify(stored, "INCIDENT_REPORTED", "incident_management");

        if (severity == Severity::CRITICAL) {
            notify(stored, "CRITICAL_ALERT", "executive_team");
        }

        return stored.id;
    }

    void assign(
        const string& incidentId,
        const string& actorId,
        const string& assigneeId
    ) {
        Incident& incident = requireIncident(incidentId);
        authorize(actorId, incident.severity);
        requireActor(assigneeId);

        incident.assignedTo = assigneeId;

        audit(
            incident,
            actorId,
            "ASSIGNED",
            "Assigned to " + assigneeId
        );

        notify(incident, "INCIDENT_ASSIGNED", assigneeId);
    }

    void acknowledge(
        const string& incidentId,
        const string& actorId
    ) {
        Incident& incident = requireIncident(incidentId);
        authorize(actorId, incident.severity);

        transition(
            incident,
            actorId,
            Status::ACKNOWLEDGED,
            "Incident acknowledged"
        );

        incident.acknowledged = true;

        notify(
            incident,
            "INCIDENT_ACKNOWLEDGED",
            incident.reporterId
        );
    }

    void investigate(
        const string& incidentId,
        const string& actorId
    ) {
        Incident& incident = requireIncident(incidentId);
        authorize(actorId, incident.severity);

        if (incident.assignedTo.empty()) {
            throw runtime_error("Investigation requires an assigned owner.");
        }

        transition(
            incident,
            actorId,
            Status::INVESTIGATING,
            "Investigation started"
        );
    }

    void escalate(
        const string& incidentId,
        const string& actorId,
        const string& reason,
        EscalationLevel target
    ) {
        Incident& incident = requireIncident(incidentId);
        authorize(actorId, incident.severity);

        validateText(reason, "Escalation reason", 1000);

        if (
            incident.status == Status::RESOLVED ||
            incident.status == Status::CLOSED
        ) {
            throw runtime_error("Cannot escalate a completed incident.");
        }

        if (
            static_cast<int>(target) <=
            static_cast<int>(incident.escalationLevel)
        ) {
            throw runtime_error("Escalation level must increase.");
        }

        incident.escalationLevel = target;

        if (incident.status != Status::ESCALATED) {
            transition(
                incident,
                actorId,
                Status::ESCALATED,
                reason
            );
        } else {
            audit(
                incident,
                actorId,
                "ESCALATED_AGAIN",
                reason
            );
        }

        string recipient =
            target == EscalationLevel::EXECUTIVE
            ? "executive_team"
            : "management_level_" +
              to_string(static_cast<int>(target));

        notify(incident, "INCIDENT_ESCALATED", recipient);
    }

    void resolve(
        const string& incidentId,
        const string& actorId,
        const string& notes
    ) {
        Incident& incident = requireIncident(incidentId);
        authorize(actorId, incident.severity);

        validateText(notes, "Resolution notes", 3000);

        transition(
            incident,
            actorId,
            Status::RESOLVED,
            notes
        );

        incident.resolved = true;
        incident.resolutionNotes = notes;

        notify(
            incident,
            "INCIDENT_RESOLVED",
            incident.reporterId
        );
    }

    void close(
        const string& incidentId,
        const string& actorId
    ) {
        Incident& incident = requireIncident(incidentId);
        authorize(actorId, incident.severity);

        if (
            !incident.resolved ||
            incident.resolutionNotes.empty()
        ) {
            throw runtime_error("Resolution evidence is mandatory.");
        }

        transition(
            incident,
            actorId,
            Status::CLOSED,
            "Administrative closure"
        );
    }

    void reopen(
        const string& incidentId,
        const string& actorId,
        const string& reason
    ) {
        Incident& incident = requireIncident(incidentId);
        authorize(actorId, incident.severity);

        validateText(reason, "Reopening reason", 1000);

        transition(
            incident,
            actorId,
            Status::INVESTIGATING,
            reason
        );

        incident.resolved = false;
        incident.resolutionNotes.clear();
    }

    void addStatusCheck(
        const string& incidentId,
        const string& actorId,
        const string& name,
        bool required,
        bool passed
    ) {
        Incident& incident = requireIncident(incidentId);
        authorize(actorId, incident.severity);

        validateText(name, "Status check name", 100);

        incident.checks.push_back({
            name,
            required,
            passed,
            true
        });

        audit(
            incident,
            actorId,
            "STATUS_CHECK_RECORDED",
            name + (passed ? " passed" : " failed")
        );
    }

    vector<string> evaluateMergeEligibility(
        const string& incidentId,
        const GovernancePolicy& policy
    ) {
        const Incident& incident = requireIncident(incidentId);
        vector<string> blockers;

        if (
            policy.requireResolvedIncident &&
            !incident.resolved
        ) {
            blockers.push_back("Incident is not resolved.");
        }

        if (
            policy.requireAssignedOwner &&
            incident.assignedTo.empty()
        ) {
            blockers.push_back("Incident has no assigned owner.");
        }

        if (
            policy.requireResolutionEvidence &&
            incident.resolutionNotes.empty()
        ) {
            blockers.push_back("Resolution evidence is missing.");
        }

        if (policy.requireStatusChecks) {
            for (const auto& check : incident.checks) {
                if (
                    check.required &&
                    (!check.completed || !check.passed)
                ) {
                    blockers.push_back(
                        "Required check failed: " + check.name
                    );
                }
            }
        }

        return blockers;
    }

    vector<string> deadlineBreaches(
        chrono::system_clock::time_point now =
            chrono::system_clock::now()
    ) {
        vector<string> breaches;

        for (const auto& [id, incident] : incidents) {
            if (
                incident.status == Status::RESOLVED ||
                incident.status == Status::CLOSED
            ) {
                continue;
            }

            if (
                !incident.acknowledged &&
                now > incident.acknowledgementDeadline
            ) {
                breaches.push_back(
                    id + ": acknowledgement deadline exceeded"
                );
            } else if (now > incident.resolutionDeadline) {
                breaches.push_back(
                    id + ": resolution deadline exceeded"
                );
            }
        }

        return breaches;
    }

    void printDashboard() const {
        map<Severity, int> severityCounts;
        map<Status, int> statusCounts;

        for (const auto& [id, incident] : incidents) {
            severityCounts[incident.severity]++;
            statusCounts[incident.status]++;
        }

        cout << "\nESCALATION GOVERNANCE DASHBOARD\n";
        cout << "====================================\n";
        cout << "Total incidents: " << incidents.size() << '\n';

        for (const auto& [severity, count] : severityCounts) {
            cout << toString(severity) << ": " << count << '\n';
        }

        cout << "\nSTATUS DISTRIBUTION\n";

        for (const auto& [status, count] : statusCounts) {
            cout << toString(status) << ": " << count << '\n';
        }

        cout << "\nINCIDENT REGISTER\n";

        for (const auto& [id, incident] : incidents) {
            cout << id
                 << " | " << incident.title
                 << " | " << toString(incident.severity)
                 << " | " << toString(incident.status)
                 << " | " << toString(incident.escalationLevel)
                 << '\n';
        }
    }

    void printNotifications() const {
        cout << "\nNOTIFICATION LOG\n";

        for (const string& message : notificationLog) {
            cout << message << '\n';
        }
    }
};

int main() {
    try {
        GovernanceEngine engine;

        engine.registerActor({
            "U001", "Operations Reporter", "reporter", "Operations"
        });

        engine.registerActor({
            "U002", "Technical Responder", "responder", "Technology"
        });

        engine.registerActor({
            "U003", "Incident Manager",
            "incident_manager", "Operations"
        });

        engine.registerActor({
            "U004", "Executive Director",
            "administrator", "Executive"
        });

        string id = engine.report(
            "U001",
            "Enterprise payment infrastructure failure",
            "Payment transactions are failing across production.",
            "Technology",
            "Operations",
            Severity::CRITICAL,
            {"payments", "production", "availability"}
        );

        engine.assign(id, "U003", "U002");
        engine.acknowledge(id, "U003");
        engine.investigate(id, "U002");

        engine.escalate(
            id,
            "U003",
            "Customer transactions are affected.",
            EscalationLevel::EXECUTIVE
        );

        engine.addStatusCheck(
            id,
            "U003",
            "Database availability",
            true,
            true
        );

        engine.addStatusCheck(
            id,
            "U003",
            "Payment transaction validation",
            true,
            true
        );

        GovernancePolicy policy;
        policy.requireResolvedIncident = true;
        policy.requireStatusChecks = true;
        policy.requireAssignedOwner = true;
        policy.requireResolutionEvidence = true;

        cout << "\nPRE-RESOLUTION GOVERNANCE CHECK\n";

        for (const string& blocker :
             engine.evaluateMergeEligibility(id, policy)) {
            cout << "BLOCKED: " << blocker << '\n';
        }

        engine.resolve(
            id,
            "U003",
            "Database recovered and payment transactions verified."
        );

        cout << "\nPOST-RESOLUTION GOVERNANCE CHECK\n";

        auto blockers = engine.evaluateMergeEligibility(id, policy);

        if (blockers.empty()) {
            cout << "ELIGIBLE: All configured incident conditions passed.\n";
        } else {
            for (const string& blocker : blockers) {
                cout << "BLOCKED: " << blocker << '\n';
            }
        }

        engine.close(id, "U003");

        engine.printDashboard();
        engine.printNotifications();

        cout << "\nDEADLINE BREACH REPORT\n";

        for (const string& breach : engine.deadlineBreaches()) {
            cout << breach << '\n';
        }

        // A completed incident cannot be investigated again unless reopened.
        try {
            engine.investigate(id, "U002");
        } catch (const exception& error) {
            cout << "\nExpected state validation: "
                 << error.what() << '\n';
        }

        assert(blockers.empty());

    } catch (const exception& error) {
        cerr << "Application failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
