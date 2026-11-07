#include <algorithm>
#include <chrono>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class ConflictType {
    Communication,
    RoleAmbiguity,
    ResourceAllocation,
    Performance,
    PersonalDisagreement,
    PriorityMismatch,
    WorkingStyle
};

enum class Severity {
    Low = 1,
    Medium = 2,
    High = 3,
    Critical = 4
};

enum class Status {
    Reported,
    Assessment,
    Discussion,
    Mediation,
    Resolved,
    Escalated,
    Closed
};

enum class ResolutionMethod {
    Collaboration,
    Compromise,
    Accommodation,
    Negotiation,
    ManagerDecision,
    FormalEscalation
};

string toString(Status status) {
    switch (status) {
        case Status::Reported: return "Reported";
        case Status::Assessment: return "Assessment";
        case Status::Discussion: return "Discussion";
        case Status::Mediation: return "Mediation";
        case Status::Resolved: return "Resolved";
        case Status::Escalated: return "Escalated";
        case Status::Closed: return "Closed";
    }
    throw logic_error("Unknown status");
}

string toString(Severity severity) {
    switch (severity) {
        case Severity::Low: return "Low";
        case Severity::Medium: return "Medium";
        case Severity::High: return "High";
        case Severity::Critical: return "Critical";
    }
    throw logic_error("Unknown severity");
}

string toString(ResolutionMethod method) {
    switch (method) {
        case ResolutionMethod::Collaboration: return "Collaboration";
        case ResolutionMethod::Compromise: return "Compromise";
        case ResolutionMethod::Accommodation: return "Accommodation";
        case ResolutionMethod::Negotiation: return "Negotiation";
        case ResolutionMethod::ManagerDecision: return "Manager decision";
        case ResolutionMethod::FormalEscalation: return "Formal escalation";
    }
    throw logic_error("Unknown method");
}

struct TeamMember {
    string id;
    string name;
    string role;
    string department;
    bool active = true;
};

struct Agreement {
    ResolutionMethod method;
    vector<string> actions;
    vector<string> criteria;
    set<string> responsibleMembers;
    set<string> acceptedBy;
    string deadline;
};

struct AuditEvent {
    string caseId;
    string actorId;
    string action;
    string timestamp;
};

struct ConflictCase {
    string id;
    string title;
    string description;
    ConflictType type;
    Severity severity;
    string reporterId;
    set<string> participants;
    Status status = Status::Reported;
    string mediatorId;
    vector<string> discussionNotes;
    vector<string> history;
    Agreement agreement;
    bool hasAgreement = false;
};

class ConflictManager {
private:
    map<string, TeamMember> members;
    map<string, ConflictCase> cases;
    vector<AuditEvent> audit;

    static string timestamp() {
        auto now = chrono::system_clock::now();
        time_t time = chrono::system_clock::to_time_t(now);

        tm utc{};

#ifdef _WIN32
        gmtime_s(&utc, &time);
#else
        gmtime_r(&time, &utc);
#endif

        stringstream stream;
        stream << put_time(&utc, "%Y-%m-%dT%H:%M:%SZ");
        return stream.str();
    }

    void log(
        const string& caseId,
        const string& actor,
        const string& action
    ) {
        audit.push_back({
            caseId,
            actor,
            action,
            timestamp()
        });
    }

    ConflictCase& getCase(const string& id) {
        auto it = cases.find(id);

        if (it == cases.end()) {
            throw invalid_argument("Conflict case not found");
        }

        return it->second;
    }

    const TeamMember& getMember(const string& id) const {
        auto it = members.find(id);

        if (it == members.end() || !it->second.active) {
            throw invalid_argument("Member unavailable");
        }

        return it->second;
    }

    static bool validTransition(Status current, Status next) {
        static const map<Status, set<Status>> allowed = {
            {Status::Reported, {
                Status::Assessment, Status::Escalated
            }},
            {Status::Assessment, {
                Status::Discussion, Status::Mediation,
                Status::Escalated
            }},
            {Status::Discussion, {
                Status::Mediation, Status::Resolved,
                Status::Escalated
            }},
            {Status::Mediation, {
                Status::Discussion, Status::Resolved,
                Status::Escalated
            }},
            {Status::Resolved, {
                Status::Closed, Status::Escalated
            }},
            {Status::Escalated, {Status::Closed}},
            {Status::Closed, {}}
        };

        auto it = allowed.find(current);

        return it != allowed.end() &&
               it->second.count(next) > 0;
    }

public:
    void registerMember(const TeamMember& member) {
        if (member.id.empty() || member.name.empty() ||
            member.role.empty() || member.department.empty()) {
            throw invalid_argument("Member fields cannot be empty");
        }

        if (members.count(member.id)) {
            throw invalid_argument("Duplicate member ID");
        }

        members.emplace(member.id, member);
    }

    void createCase(const ConflictCase& conflict) {
        if (conflict.id.empty() || conflict.title.empty() ||
            conflict.description.empty()) {
            throw invalid_argument("Case fields cannot be empty");
        }

        if (conflict.participants.size() < 2) {
            throw invalid_argument("At least two participants required");
        }

        if (!conflict.participants.count(conflict.reporterId)) {
            throw invalid_argument("Reporter must be a participant");
        }

        if (cases.count(conflict.id)) {
            throw invalid_argument("Duplicate case ID");
        }

        getMember(conflict.reporterId);

        for (const auto& id : conflict.participants) {
            getMember(id);
        }

        cases.emplace(conflict.id, conflict);
        log(conflict.id, conflict.reporterId, "CASE_CREATED");
    }

    void assignMediator(
        const string& caseId,
        const string& mediatorId
    ) {
        ConflictCase& conflict = getCase(caseId);
        getMember(mediatorId);

        if (conflict.participants.count(mediatorId)) {
            throw invalid_argument(
                "Mediator cannot be a conflict participant"
            );
        }

        conflict.mediatorId = mediatorId;
        log(caseId, mediatorId, "MEDIATOR_ASSIGNED");
    }

    void transition(
        const string& caseId,
        Status next,
        const string& actorId
    ) {
        ConflictCase& conflict = getCase(caseId);
        getMember(actorId);

        if (!validTransition(conflict.status, next)) {
            throw logic_error(
                "Invalid transition from " +
                toString(conflict.status) + " to " +
                toString(next)
            );
        }

        Status previous = conflict.status;
        conflict.status = next;

        conflict.history.push_back(
            toString(previous) + " -> " + toString(next)
        );

        log(
            caseId,
            actorId,
            "STATUS_CHANGED:" + toString(previous) +
            ":" + toString(next)
        );
    }

    void addDiscussion(
        const string& caseId,
        const string& actorId,
        const string& message
    ) {
        ConflictCase& conflict = getCase(caseId);
        getMember(actorId);

        bool authorized =
            conflict.participants.count(actorId) ||
            conflict.mediatorId == actorId;

        if (!authorized) {
            throw logic_error("Discussion access denied");
        }

        if (message.empty()) {
            throw invalid_argument("Discussion cannot be empty");
        }

        if (conflict.status != Status::Assessment &&
            conflict.status != Status::Discussion &&
            conflict.status != Status::Mediation) {
            throw logic_error("Discussion is not permitted");
        }

        conflict.discussionNotes.push_back(message);
        log(caseId, actorId, "DISCUSSION_ADDED");
    }

    ResolutionMethod recommendMethod(const string& caseId) {
        const ConflictCase& conflict = cases.at(caseId);

        if (conflict.severity == Severity::Critical) {
            return ResolutionMethod::FormalEscalation;
        }

        if (conflict.type == ConflictType::ResourceAllocation) {
            return ResolutionMethod::Negotiation;
        }

        if (conflict.type == ConflictType::PriorityMismatch) {
            return ResolutionMethod::Collaboration;
        }

        if (conflict.severity == Severity::High) {
            return ResolutionMethod::Collaboration;
        }

        return ResolutionMethod::Compromise;
    }

    void createAgreement(
        const string& caseId,
        const string& actorId,
        const Agreement& agreement
    ) {
        ConflictCase& conflict = getCase(caseId);
        getMember(actorId);

        if (conflict.status != Status::Discussion &&
            conflict.status != Status::Mediation) {
            throw logic_error(
                "Agreement requires discussion or mediation"
            );
        }

        if (agreement.actions.empty() ||
            agreement.criteria.empty()) {
            throw invalid_argument(
                "Actions and success criteria are required"
            );
        }

        if (agreement.responsibleMembers.empty()) {
            throw invalid_argument(
                "Responsible members are required"
            );
        }

        for (const auto& id : agreement.responsibleMembers) {
            if (!conflict.participants.count(id)) {
                throw invalid_argument(
                    "Responsible member is not a participant"
                );
            }
        }

        conflict.agreement = agreement;
        conflict.hasAgreement = true;

        log(caseId, actorId, "AGREEMENT_CREATED");
    }

    void acceptAgreement(
        const string& caseId,
        const string& memberId
    ) {
        ConflictCase& conflict = getCase(caseId);
        getMember(memberId);

        if (!conflict.hasAgreement) {
            throw logic_error("No agreement exists");
        }

        if (!conflict.participants.count(memberId)) {
            throw logic_error("Only participants can accept");
        }

        conflict.agreement.acceptedBy.insert(memberId);
        log(caseId, memberId, "AGREEMENT_ACCEPTED");
    }

    void resolve(
        const string& caseId,
        const string& managerId
    ) {
        ConflictCase& conflict = getCase(caseId);
        getMember(managerId);

        if (!conflict.hasAgreement) {
            throw logic_error("Agreement is missing");
        }

        if (conflict.agreement.acceptedBy !=
            conflict.participants) {
            throw logic_error(
                "All participants must accept the agreement"
            );
        }

        transition(caseId, Status::Resolved, managerId);
    }

    void printReport() const {
        map<Status, int> statusCounts;

        for (const auto& [id, conflict] : cases) {
            statusCounts[conflict.status]++;
        }

        cout << "\nCONFLICT MANAGEMENT REPORT\n";
        cout << "Total cases: " << cases.size() << '\n';

        for (const auto& [status, count] : statusCounts) {
            cout << toString(status) << ": " << count << '\n';
        }

        cout << "\nCASE DETAILS\n";

        for (const auto& [id, conflict] : cases) {
            cout << id << " | "
                 << conflict.title << " | "
                 << toString(conflict.severity) << " | "
                 << toString(conflict.status) << '\n';
        }

        cout << "\nAUDIT EVENTS: " << audit.size() << '\n';
    }
};

int main() {
    try {
        ConflictManager manager;

        manager.registerMember({
            "E01", "Ananya", "Developer", "Engineering", true
        });

        manager.registerMember({
            "E02", "Rahul", "Designer", "Product", true
        });

        manager.registerMember({
            "E03", "Priya", "Manager", "Management", true
        });

        manager.registerMember({
            "E04", "Arjun", "Mediator", "Human Resources", true
        });

        ConflictCase conflict{
            "CF-3001",
            "Release priority disagreement",
            "Engineering and Product disagree about release scope.",
            ConflictType::PriorityMismatch,
            Severity::Medium,
            "E01",
            {"E01", "E02"}
        };

        manager.createCase(conflict);
        manager.assignMediator("CF-3001", "E04");

        manager.transition(
            "CF-3001", Status::Assessment, "E03"
        );

        manager.transition(
            "CF-3001", Status::Discussion, "E03"
        );

        manager.addDiscussion(
            "CF-3001",
            "E01",
            "Engineering needs sufficient testing time."
        );

        manager.addDiscussion(
            "CF-3001",
            "E02",
            "Product needs the core release features."
        );

        Agreement agreement{
            manager.recommendMethod("CF-3001"),
            {
                "Deliver core features first",
                "Move optional features to the next iteration",
                "Conduct joint release testing"
            },
            {
                "Acceptance tests pass",
                "Both teams approve the release plan"
            },
            {"E01", "E02"},
            {},
            "2026-11-20"
        };

        manager.createAgreement(
            "CF-3001", "E03", agreement
        );

        manager.acceptAgreement("CF-3001", "E01");
        manager.acceptAgreement("CF-3001", "E02");

        manager.resolve("CF-3001", "E03");

        manager.transition(
            "CF-3001", Status::Closed, "E03"
        );

        manager.printReport();

        cout << "\nResolution method: "
             << toString(
                 manager.recommendMethod("CF-3001")
             ) << '\n';

        try {
            manager.transition(
                "CF-3001", Status::Resolved, "E03"
            );
        } catch (const exception& error) {
            cout << "\nExpected failure: "
                 << error.what() << '\n';
        }

    } catch (const exception& error) {
        cerr << "Application error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
