#include <algorithm>
#include <chrono>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class MeetingStatus {
    Scheduled,
    InProgress,
    Completed,
    Cancelled
};

enum class Priority {
    Low,
    Medium,
    High,
    Critical
};

enum class ActionStatus {
    Open,
    InProgress,
    Blocked,
    Completed
};

enum class Role {
    Organizer,
    Chairperson,
    Member,
    Observer
};

string toString(MeetingStatus status) {
    switch (status) {
        case MeetingStatus::Scheduled: return "Scheduled";
        case MeetingStatus::InProgress: return "In Progress";
        case MeetingStatus::Completed: return "Completed";
        case MeetingStatus::Cancelled: return "Cancelled";
    }
    return "Unknown";
}

string toString(ActionStatus status) {
    switch (status) {
        case ActionStatus::Open: return "Open";
        case ActionStatus::InProgress: return "In Progress";
        case ActionStatus::Blocked: return "Blocked";
        case ActionStatus::Completed: return "Completed";
    }
    return "Unknown";
}

string toString(Priority priority) {
    switch (priority) {
        case Priority::Low: return "Low";
        case Priority::Medium: return "Medium";
        case Priority::High: return "High";
        case Priority::Critical: return "Critical";
    }
    return "Unknown";
}

class MeetingException : public runtime_error {
public:
    explicit MeetingException(const string& message)
        : runtime_error(message) {}
};

struct Participant {
    string id;
    string name;
    string email;
    Role role;
    bool attended = false;
};

struct AgendaItem {
    int id;
    string title;
    string ownerId;
    int durationMinutes;
    Priority priority;
    bool completed = false;
    string notes;
};

struct Decision {
    int id;
    string description;
    string recordedBy;
    string rationale;
    time_t recordedAt;
};

struct ActionItem {
    int id;
    string description;
    string assigneeId;
    time_t dueDate;
    Priority priority;
    ActionStatus status = ActionStatus::Open;
    string completionNotes;
};

struct Meeting {
    string id;
    string title;
    string project;
    string organizerId;
    time_t scheduledAt;
    int durationMinutes;
    string location;

    MeetingStatus status = MeetingStatus::Scheduled;

    map<string, Participant> participants;
    vector<AgendaItem> agenda;
    vector<Decision> decisions;
    vector<ActionItem> actions;
    string minutes;

    time_t endTime() const {
        return scheduledAt + durationMinutes * 60;
    }

    void validate() const {
        if (id.empty() || title.empty() ||
            project.empty() || location.empty()) {
            throw MeetingException("Required meeting fields are missing.");
        }

        if (durationMinutes <= 0 || durationMinutes > 1440) {
            throw MeetingException("Invalid meeting duration.");
        }

        if (participants.find(organizerId) == participants.end()) {
            throw MeetingException("Organizer must be a participant.");
        }
    }

    void requireParticipant(const string& participantId) const {
        if (participants.find(participantId) == participants.end()) {
            throw MeetingException("Unknown participant.");
        }
    }

    void addAgendaItem(AgendaItem item) {
        if (status != MeetingStatus::Scheduled) {
            throw MeetingException("Agenda is locked.");
        }

        requireParticipant(item.ownerId);

        if (item.title.empty() || item.durationMinutes <= 0) {
            throw MeetingException("Invalid agenda item.");
        }

        auto duplicate = find_if(
            agenda.begin(), agenda.end(),
            [&](const AgendaItem& a) {
                return a.id == item.id;
            }
        );

        if (duplicate != agenda.end()) {
            throw MeetingException("Duplicate agenda item ID.");
        }

        agenda.push_back(move(item));
    }

    void markAttendance(const string& participantId, bool attended) {
        if (status != MeetingStatus::Scheduled &&
            status != MeetingStatus::InProgress) {
            throw MeetingException("Attendance is closed.");
        }

        requireParticipant(participantId);
        participants.at(participantId).attended = attended;
    }

    void start() {
        if (status != MeetingStatus::Scheduled) {
            throw MeetingException("Invalid start transition.");
        }

        if (agenda.empty()) {
            throw MeetingException("Meeting requires an agenda.");
        }

        status = MeetingStatus::InProgress;
    }

    void completeAgendaItem(int itemId, const string& notes) {
        if (status != MeetingStatus::InProgress) {
            throw MeetingException("Meeting is not active.");
        }

        auto item = find_if(
            agenda.begin(), agenda.end(),
            [&](const AgendaItem& a) {
                return a.id == itemId;
            }
        );

        if (item == agenda.end()) {
            throw MeetingException("Agenda item not found.");
        }

        item->completed = true;
        item->notes = notes;
    }

    void recordDecision(
        int decisionId,
        const string& description,
        const string& recordedBy,
        const string& rationale
    ) {
        if (status != MeetingStatus::InProgress) {
            throw MeetingException("Decisions require an active meeting.");
        }

        requireParticipant(recordedBy);

        if (description.empty()) {
            throw MeetingException("Decision cannot be empty.");
        }

        decisions.push_back({
            decisionId,
            description,
            recordedBy,
            rationale,
            time(nullptr)
        });
    }

    void createAction(ActionItem action) {
        if (status != MeetingStatus::InProgress) {
            throw MeetingException("Meeting is not active.");
        }

        requireParticipant(action.assigneeId);

        if (action.description.empty()) {
            throw MeetingException("Action description is required.");
        }

        if (action.dueDate <= 0) {
            throw MeetingException("Invalid action deadline.");
        }

        auto duplicate = find_if(
            actions.begin(), actions.end(),
            [&](const ActionItem& a) {
                return a.id == action.id;
            }
        );

        if (duplicate != actions.end()) {
            throw MeetingException("Duplicate action ID.");
        }

        actions.push_back(move(action));
    }

    void updateAction(
        int actionId,
        ActionStatus newStatus,
        const string& evidence = ""
    ) {
        auto action = find_if(
            actions.begin(), actions.end(),
            [&](const ActionItem& a) {
                return a.id == actionId;
            }
        );

        if (action == actions.end()) {
            throw MeetingException("Action not found.");
        }

        if (action->status == ActionStatus::Completed) {
            throw MeetingException("Completed action is immutable.");
        }

        if (newStatus == ActionStatus::Completed && evidence.empty()) {
            throw MeetingException(
                "Completion evidence is required."
            );
        }

        action->status = newStatus;
        action->completionNotes = evidence;
    }

    void close(const string& meetingMinutes) {
        if (status != MeetingStatus::InProgress) {
            throw MeetingException("Only active meetings can close.");
        }

        if (meetingMinutes.empty()) {
            throw MeetingException("Meeting minutes are required.");
        }

        minutes = meetingMinutes;
        status = MeetingStatus::Completed;
    }

    void cancel(const string& reason) {
        if (status == MeetingStatus::Completed ||
            status == MeetingStatus::Cancelled) {
            throw MeetingException("Meeting cannot be cancelled.");
        }

        if (reason.empty()) {
            throw MeetingException("Cancellation reason is required.");
        }

        minutes = "Cancelled: " + reason;
        status = MeetingStatus::Cancelled;
    }
};

class RepositoryGovernance {
private:
    map<string, Meeting> meetings;

public:
    void schedule(Meeting meeting) {
        meeting.validate();

        if (meetings.count(meeting.id)) {
            throw MeetingException("Duplicate meeting ID.");
        }

        for (const auto& entry : meetings) {
            const Meeting& existing = entry.second;

            if (existing.organizerId != meeting.organizerId) {
                continue;
            }

            if (existing.status != MeetingStatus::Scheduled &&
                existing.status != MeetingStatus::InProgress) {
                continue;
            }

            bool overlap =
                meeting.scheduledAt < existing.endTime() &&
                existing.scheduledAt < meeting.endTime();

            if (overlap) {
                throw MeetingException(
                    "Organizer has a scheduling conflict."
                );
            }
        }

        meetings.emplace(meeting.id, move(meeting));
    }

    Meeting& getMeeting(const string& id) {
        auto it = meetings.find(id);

        if (it == meetings.end()) {
            throw MeetingException("Meeting not found.");
        }

        return it->second;
    }

    vector<const Meeting*> upcoming(time_t reference) const {
        vector<const Meeting*> result;

        for (const auto& entry : meetings) {
            const Meeting& meeting = entry.second;

            if (meeting.status == MeetingStatus::Scheduled &&
                meeting.scheduledAt >= reference) {
                result.push_back(&meeting);
            }
        }

        sort(
            result.begin(), result.end(),
            [](const Meeting* a, const Meeting* b) {
                return a->scheduledAt < b->scheduledAt;
            }
        );

        return result;
    }

    vector<pair<string, const ActionItem*>> overdueActions(
        time_t reference
    ) const {
        vector<pair<string, const ActionItem*>> result;

        for (const auto& entry : meetings) {
            for (const auto& action : entry.second.actions) {
                if (action.dueDate < reference &&
                    action.status != ActionStatus::Completed) {
                    result.emplace_back(entry.first, &action);
                }
            }
        }

        return result;
    }

    void projectReport(const string& project) const {
        int total = 0;
        int completed = 0;
        int cancelled = 0;
        int decisions = 0;
        int actions = 0;
        int completedActions = 0;
        int overdue = 0;

        time_t now = time(nullptr);

        for (const auto& entry : meetings) {
            const Meeting& meeting = entry.second;

            if (meeting.project != project) {
                continue;
            }

            total++;

            if (meeting.status == MeetingStatus::Completed) {
                completed++;
            }

            if (meeting.status == MeetingStatus::Cancelled) {
                cancelled++;
            }

            decisions += static_cast<int>(meeting.decisions.size());

            for (const auto& action : meeting.actions) {
                actions++;

                if (action.status == ActionStatus::Completed) {
                    completedActions++;
                } else if (action.dueDate < now) {
                    overdue++;
                }
            }
        }

        cout << "\nPROJECT MANAGEMENT REPORT\n";
        cout << "Project: " << project << '\n';
        cout << "Total meetings: " << total << '\n';
        cout << "Completed meetings: " << completed << '\n';
        cout << "Cancelled meetings: " << cancelled << '\n';
        cout << "Decisions recorded: " << decisions << '\n';
        cout << "Total actions: " << actions << '\n';
        cout << "Completed actions: " << completedActions << '\n';
        cout << "Overdue actions: " << overdue << '\n';
    }

    void printMeeting(const Meeting& meeting) const {
        cout << "\nMEETING DETAILS\n";
        cout << "ID: " << meeting.id << '\n';
        cout << "Title: " << meeting.title << '\n';
        cout << "Project: " << meeting.project << '\n';
        cout << "Status: " << toString(meeting.status) << '\n';

        cout << "\nAGENDA\n";

        for (const auto& item : meeting.agenda) {
            cout << item.id << ". " << item.title
                 << " | " << item.durationMinutes << " minutes"
                 << " | " << toString(item.priority)
                 << " | "
                 << (item.completed ? "Completed" : "Pending")
                 << '\n';
        }

        cout << "\nDECISIONS\n";

        for (const auto& decision : meeting.decisions) {
            cout << "- " << decision.description << '\n';
        }

        cout << "\nACTION ITEMS\n";

        for (const auto& action : meeting.actions) {
            cout << "- " << action.description
                 << " | Owner: " << action.assigneeId
                 << " | " << toString(action.status)
                 << " | " << toString(action.priority)
                 << '\n';
        }
    }
};

time_t futureTime(int days) {
    return time(nullptr) + days * 24 * 60 * 60;
}

int main() {
    try {
        RepositoryGovernance manager;

        Meeting meeting;
        meeting.id = "M001";
        meeting.title = "Project Delivery Review";
        meeting.project = "Enterprise Platform";
        meeting.organizerId = "P001";
        meeting.scheduledAt = futureTime(1);
        meeting.durationMinutes = 90;
        meeting.location = "Conference Room A";

        meeting.participants.emplace(
            "P001",
            Participant{
                "P001", "Project Manager",
                "manager@example.com", Role::Organizer
            }
        );

        meeting.participants.emplace(
            "P002",
            Participant{
                "P002", "Technical Lead",
                "technical@example.com", Role::Member
            }
        );

        meeting.participants.emplace(
            "P003",
            Participant{
                "P003", "Business Analyst",
                "analyst@example.com", Role::Member
            }
        );

        manager.schedule(meeting);

        Meeting& active = manager.getMeeting("M001");

        active.addAgendaItem({
            1, "Delivery progress", "P001",
            20, Priority::High
        });

        active.addAgendaItem({
            2, "Technical risks", "P002",
            30, Priority::Critical
        });

        active.markAttendance("P001", true);
        active.markAttendance("P002", true);
        active.markAttendance("P003", true);

        active.start();

        active.completeAgendaItem(
            1, "Milestones reviewed and accepted."
        );

        active.recordDecision(
            1,
            "Approve the revised project timeline.",
            "P001",
            "Resource capacity and delivery estimates reviewed."
        );

        active.createAction({
            1,
            "Prepare technical risk mitigation plan.",
            "P002",
            futureTime(5),
            Priority::High
        });

        active.updateAction(
            1,
            ActionStatus::InProgress
        );

        active.close(
            "Project timeline approved. Risk mitigation assigned."
        );

        manager.printMeeting(active);
        manager.projectReport("Enterprise Platform");

        cout << "\nUPCOMING MEETINGS\n";

        for (const Meeting* item : manager.upcoming(time(nullptr))) {
            cout << item->id << " | " << item->title << '\n';
        }

        cout << "\nOVERDUE ACTIONS\n";

        auto overdue = manager.overdueActions(time(nullptr));

        for (const auto& item : overdue) {
            cout << item.second->description
                 << " | Meeting: " << item.first << '\n';
        }

        // Invalid transition must not modify meeting state.
        try {
            active.start();
        } catch (const MeetingException& error) {
            cout << "\nExpected state protection: "
                 << error.what() << '\n';
        }

        // Invalid participant must be rejected.
        try {
            active.markAttendance("UNKNOWN", true);
        } catch (const MeetingException& error) {
            cout << "Expected validation: "
                 << error.what() << '\n';
        }

        // Duplicate meeting IDs must be rejected.
        try {
            manager.schedule(active);
        } catch (const MeetingException& error) {
            cout << "Expected duplicate protection: "
                 << error.what() << '\n';
        }

    } catch (const exception& error) {
        cerr << "Application error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
