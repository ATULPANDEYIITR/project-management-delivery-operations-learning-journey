/*
 * PROJECT COMMUNICATION MANAGEMENT
 * Introduction to Project Communication
 *
 * C++17 repository-independent communication governance engine.
 *
 * Capabilities:
 * - Stakeholder classification
 * - Communication policy evaluation
 * - Audience authorization
 * - Message lifecycle management
 * - Delivery and acknowledgement tracking
 * - Meeting and decision management
 * - Action-item state transitions
 * - Escalation
 * - Communication reporting
 * - Audit logging
 *
 * Compile:
 * g++ -std=c++17 -O2 -Wall -Wextra -pedantic project_communication.cpp -o project_communication
 *
 * Run:
 * ./project_communication
 */

#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

// ============================================================
// ENUMERATIONS
// ============================================================

enum class Role {
    ProjectManager,
    Sponsor,
    Developer,
    Client,
    Vendor,
    Executive
};

enum class Channel {
    Email,
    Meeting,
    Chat,
    Report,
    Phone,
    Portal
};

enum class Purpose {
    Information,
    StatusUpdate,
    Decision,
    Request,
    Escalation
};

enum class Confidentiality {
    Public = 1,
    Internal = 2,
    Confidential = 3,
    Restricted = 4
};

enum class MessageState {
    Draft,
    Sent,
    Acknowledged,
    Escalated
};

enum class ActionState {
    Open,
    InProgress,
    Blocked,
    Completed,
    Cancelled
};

// ============================================================
// ENUMERATION CONVERSION
// ============================================================

string toString(Role role) {
    switch (role) {
        case Role::ProjectManager: return "Project Manager";
        case Role::Sponsor: return "Sponsor";
        case Role::Developer: return "Developer";
        case Role::Client: return "Client";
        case Role::Vendor: return "Vendor";
        case Role::Executive: return "Executive";
    }
    throw runtime_error("Unknown role.");
}

string toString(Channel channel) {
    switch (channel) {
        case Channel::Email: return "Email";
        case Channel::Meeting: return "Meeting";
        case Channel::Chat: return "Chat";
        case Channel::Report: return "Report";
        case Channel::Phone: return "Phone";
        case Channel::Portal: return "Portal";
    }
    throw runtime_error("Unknown channel.");
}

string toString(Purpose purpose) {
    switch (purpose) {
        case Purpose::Information: return "Information";
        case Purpose::StatusUpdate: return "Status Update";
        case Purpose::Decision: return "Decision";
        case Purpose::Request: return "Request";
        case Purpose::Escalation: return "Escalation";
    }
    throw runtime_error("Unknown purpose.");
}

string toString(MessageState state) {
    switch (state) {
        case MessageState::Draft: return "Draft";
        case MessageState::Sent: return "Sent";
        case MessageState::Acknowledged: return "Acknowledged";
        case MessageState::Escalated: return "Escalated";
    }
    throw runtime_error("Unknown message state.");
}

string toString(ActionState state) {
    switch (state) {
        case ActionState::Open: return "Open";
        case ActionState::InProgress: return "In Progress";
        case ActionState::Blocked: return "Blocked";
        case ActionState::Completed: return "Completed";
        case ActionState::Cancelled: return "Cancelled";
    }
    throw runtime_error("Unknown action state.");
}

// ============================================================
// EXCEPTIONS
// ============================================================

class CommunicationError : public runtime_error {
public:
    explicit CommunicationError(const string& message)
        : runtime_error(message) {}
};

class ValidationError : public CommunicationError {
public:
    explicit ValidationError(const string& message)
        : CommunicationError(message) {}
};

class AuthorizationError : public CommunicationError {
public:
    explicit AuthorizationError(const string& message)
        : CommunicationError(message) {}
};

class NotFoundError : public CommunicationError {
public:
    explicit NotFoundError(const string& message)
        : CommunicationError(message) {}
};

class StateTransitionError : public CommunicationError {
public:
    explicit StateTransitionError(const string& message)
        : CommunicationError(message) {}
};

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

bool isBlank(const string& value) {
    return value.find_first_not_of(" \t\n\r") == string::npos;
}

void validateText(const string& value, const string& field) {
    if (isBlank(value)) {
        throw ValidationError(field + " cannot be empty.");
    }
}

using Clock = chrono::system_clock;
using TimePoint = Clock::time_point;

string formatTime(TimePoint value) {
    time_t raw = Clock::to_time_t(value);

    tm timeInfo{};

#ifdef _WIN32
    localtime_s(&timeInfo, &raw);
#else
    localtime_r(&raw, &timeInfo);
#endif

    stringstream stream;

    stream << put_time(&timeInfo, "%Y-%m-%d %H:%M:%S");

    return stream.str();
}

// ============================================================
// DOMAIN STRUCTURES
// ============================================================

struct Stakeholder {
    string id;
    string name;
    string email;
    Role role;
    int influence;
    int interest;
    Confidentiality clearance;
    bool active = true;

    void validate() const {
        validateText(id, "Stakeholder ID");
        validateText(name, "Stakeholder name");
        validateText(email, "Email");

        if (email.find('@') == string::npos) {
            throw ValidationError("Invalid email.");
        }

        if (influence < 1 || influence > 5 ||
            interest < 1 || interest > 5) {
            throw ValidationError("Influence and interest must be 1-5.");
        }
    }

    string engagementStrategy() const {
        int score = influence * interest;

        if (score >= 16) return "MANAGE CLOSELY";
        if (influence >= 4) return "KEEP SATISFIED";
        if (interest >= 4) return "KEEP INFORMED";

        return "MONITOR";
    }
};

struct CommunicationPlan {
    string id;
    string stakeholderId;
    string ownerId;
    Channel channel;
    Purpose purpose;
    string frequency;
    TimePoint nextCommunication;
    bool active = true;
};

struct Message {
    string id;
    string senderId;
    string subject;
    string body;
    Channel channel;
    Purpose purpose;
    Confidentiality confidentiality;
    vector<string> recipients;
    set<string> acknowledgements;
    MessageState state = MessageState::Draft;
    TimePoint createdAt = Clock::now();
    TimePoint sentAt{};
    bool hasBeenSent = false;
};

struct Meeting {
    string id;
    string title;
    string organizerId;
    vector<string> participants;
    TimePoint scheduledAt;
    vector<string> agenda;
    string minutes;
    bool completed = false;
};

struct Decision {
    string id;
    string meetingId;
    string description;
    string ownerId;
    bool approved;
    TimePoint decidedAt = Clock::now();
};

struct ActionItem {
    string id;
    string description;
    string assignedTo;
    string createdBy;
    TimePoint dueDate;
    ActionState state = ActionState::Open;
    bool completed = false;
};

struct AuditEvent {
    string type;
    string entityId;
    string actorId;
    TimePoint timestamp;
};

// ============================================================
// COMMUNICATION POLICY ENGINE
// ============================================================

class CommunicationPolicy {

public:

    static bool canSend(Role role, Purpose purpose) {
        if (role == Role::ProjectManager) {
            return true;
        }

        if (role == Role::Sponsor) {
            return purpose == Purpose::Information ||
                   purpose == Purpose::StatusUpdate ||
                   purpose == Purpose::Decision ||
                   purpose == Purpose::Escalation;
        }

        if (role == Role::Developer) {
            return purpose == Purpose::Information ||
                   purpose == Purpose::StatusUpdate ||
                   purpose == Purpose::Request;
        }

        if (role == Role::Client) {
            return purpose != Purpose::Escalation;
        }

        if (role == Role::Vendor) {
            return purpose == Purpose::Information ||
                   purpose == Purpose::StatusUpdate ||
                   purpose == Purpose::Request;
        }

        if (role == Role::Executive) {
            return purpose == Purpose::Information ||
                   purpose == Purpose::StatusUpdate ||
                   purpose == Purpose::Escalation;
        }

        return false;
    }

    static bool canReceive(
        const Stakeholder& stakeholder,
        Confidentiality level
    ) {
        return stakeholder.active &&
            static_cast<int>(stakeholder.clearance) >=
            static_cast<int>(level);
    }
};

// ============================================================
// REPOSITORY COMMUNICATION ENGINE
// ============================================================

class ProjectCommunicationEngine {

private:

    string projectName;

    map<string, Stakeholder> stakeholders;
    map<string, CommunicationPlan> plans;
    map<string, Message> messages;
    map<string, Meeting> meetings;
    map<string, Decision> decisions;
    map<string, ActionItem> actions;

    vector<AuditEvent> audit;

    unsigned long long sequence = 1;

    string generateId(const string& prefix) {
        return prefix + "-" + to_string(sequence++);
    }

    void recordAudit(
        const string& type,
        const string& entityId,
        const string& actorId
    ) {
        audit.push_back({
            type,
            entityId,
            actorId,
            Clock::now()
        });
    }

    const Stakeholder& getStakeholder(
        const string& stakeholderId
    ) const {

        auto iterator = stakeholders.find(stakeholderId);

        if (iterator == stakeholders.end()) {
            throw NotFoundError("Stakeholder not found: " + stakeholderId);
        }

        if (!iterator->second.active) {
            throw AuthorizationError("Stakeholder is inactive.");
        }

        return iterator->second;
    }

public:

    explicit ProjectCommunicationEngine(string name)
        : projectName(std::move(name)) {

        validateText(projectName, "Project name");
    }

    // --------------------------------------------------------
    // STAKEHOLDERS
    // --------------------------------------------------------

    void addStakeholder(const Stakeholder& stakeholder) {
        stakeholder.validate();

        if (stakeholders.count(stakeholder.id)) {
            throw ValidationError("Duplicate stakeholder ID.");
        }

        for (const auto& entry : stakeholders) {
            if (entry.second.email == stakeholder.email) {
                throw ValidationError("Duplicate stakeholder email.");
            }
        }

        stakeholders.emplace(stakeholder.id, stakeholder);

        recordAudit(
            "STAKEHOLDER_ADDED",
            stakeholder.id,
            stakeholder.id
        );
    }

    void printStakeholders() const {
        cout << "\nSTAKEHOLDER REGISTER\n";

        for (const auto& entry : stakeholders) {
            const Stakeholder& stakeholder = entry.second;

            cout << stakeholder.id
                 << " | " << stakeholder.name
                 << " | " << toString(stakeholder.role)
                 << " | " << stakeholder.engagementStrategy()
                 << '\n';
        }
    }

    // --------------------------------------------------------
    // COMMUNICATION PLANNING
    // --------------------------------------------------------

    void addPlan(const CommunicationPlan& plan) {
        getStakeholder(plan.stakeholderId);
        getStakeholder(plan.ownerId);

        validateText(plan.id, "Plan ID");
        validateText(plan.frequency, "Frequency");

        if (plans.count(plan.id)) {
            throw ValidationError("Duplicate plan ID.");
        }

        plans.emplace(plan.id, plan);

        recordAudit(
            "PLAN_CREATED",
            plan.id,
            plan.ownerId
        );
    }

    // --------------------------------------------------------
    // MESSAGE CREATION
    // --------------------------------------------------------

    string createMessage(
        const string& senderId,
        const string& subject,
        const string& body,
        Channel channel,
        Purpose purpose,
        Confidentiality confidentiality,
        const vector<string>& recipients
    ) {
        const Stakeholder& sender = getStakeholder(senderId);

        validateText(subject, "Message subject");
        validateText(body, "Message body");

        if (recipients.empty()) {
            throw ValidationError("Recipients cannot be empty.");
        }

        set<string> uniqueRecipients;

        for (const string& recipientId : recipients) {
            if (!uniqueRecipients.insert(recipientId).second) {
                throw ValidationError("Duplicate recipient.");
            }

            const Stakeholder& recipient = getStakeholder(recipientId);

            if (!CommunicationPolicy::canReceive(
                    recipient, confidentiality)) {
                throw AuthorizationError(
                    "Recipient lacks confidentiality clearance."
                );
            }
        }

        if (!CommunicationPolicy::canSend(sender.role, purpose)) {
            throw AuthorizationError(
                "Sender role is not authorized for this purpose."
            );
        }

        string id = generateId("MSG");

        Message message{
            id,
            senderId,
            subject,
            body,
            channel,
            purpose,
            confidentiality,
            recipients
        };

        messages.emplace(id, std::move(message));

        recordAudit("MESSAGE_CREATED", id, senderId);

        return id;
    }

    // --------------------------------------------------------
    // MESSAGE DISPATCH
    // --------------------------------------------------------

    void sendMessage(const string& messageId) {
        auto iterator = messages.find(messageId);

        if (iterator == messages.end()) {
            throw NotFoundError("Message not found.");
        }

        Message& message = iterator->second;

        if (message.state != MessageState::Draft) {
            throw StateTransitionError("Message is not a draft.");
        }

        // Revalidate all recipients at dispatch time.
        for (const string& recipientId : message.recipients) {
            const Stakeholder& recipient = getStakeholder(recipientId);

            if (!CommunicationPolicy::canReceive(
                    recipient, message.confidentiality)) {
                throw AuthorizationError("Dispatch authorization failed.");
            }
        }

        message.state = MessageState::Sent;
        message.sentAt = Clock::now();
        message.hasBeenSent = true;

        recordAudit(
            "MESSAGE_SENT",
            messageId,
            message.senderId
        );
    }

    void acknowledgeMessage(
        const string& messageId,
        const string& stakeholderId
    ) {
        auto iterator = messages.find(messageId);

        if (iterator == messages.end()) {
            throw NotFoundError("Message not found.");
        }

        Message& message = iterator->second;

        if (message.state != MessageState::Sent &&
            message.state != MessageState::Acknowledged) {
            throw StateTransitionError(
                "Message cannot be acknowledged."
            );
        }

        if (find(
                message.recipients.begin(),
                message.recipients.end(),
                stakeholderId
            ) == message.recipients.end()) {
            throw AuthorizationError("Stakeholder is not a recipient.");
        }

        getStakeholder(stakeholderId);

        message.acknowledgements.insert(stakeholderId);

        if (message.acknowledgements.size() == message.recipients.size()) {
            message.state = MessageState::Acknowledged;
        }

        recordAudit(
            "MESSAGE_ACKNOWLEDGED",
            messageId,
            stakeholderId
        );
    }

    vector<string> getUnacknowledged(
        const string& messageId
    ) const {
        auto iterator = messages.find(messageId);

        if (iterator == messages.end()) {
            throw NotFoundError("Message not found.");
        }

        const Message& message = iterator->second;

        vector<string> pending;

        for (const string& recipient : message.recipients) {
            if (!message.acknowledgements.count(recipient)) {
                pending.push_back(recipient);
            }
        }

        return pending;
    }

    // --------------------------------------------------------
    // MEETINGS
    // --------------------------------------------------------

    string scheduleMeeting(
        const string& organizerId,
        const string& title,
        const vector<string>& participants,
        const vector<string>& agenda,
        TimePoint scheduledAt
    ) {
        getStakeholder(organizerId);

        validateText(title, "Meeting title");

        if (participants.empty() || agenda.empty()) {
            throw ValidationError(
                "Meeting requires participants and an agenda."
            );
        }

        set<string> uniqueParticipants;

        for (const string& participant : participants) {
            getStakeholder(participant);

            if (!uniqueParticipants.insert(participant).second) {
                throw ValidationError("Duplicate meeting participant.");
            }
        }

        for (const string& item : agenda) {
            validateText(item, "Agenda item");
        }

        string id = generateId("MEET");

        meetings.emplace(
            id,
            Meeting{
                id,
                title,
                organizerId,
                participants,
                scheduledAt,
                agenda
            }
        );

        recordAudit("MEETING_SCHEDULED", id, organizerId);

        return id;
    }

    void completeMeeting(
        const string& meetingId,
        const string& organizerId,
        const string& minutes
    ) {
        auto iterator = meetings.find(meetingId);

        if (iterator == meetings.end()) {
            throw NotFoundError("Meeting not found.");
        }

        Meeting& meeting = iterator->second;

        if (meeting.organizerId != organizerId) {
            throw AuthorizationError("Only the organizer can finalize.");
        }

        if (meeting.completed) {
            throw StateTransitionError("Meeting already completed.");
        }

        validateText(minutes, "Meeting minutes");

        meeting.minutes = minutes;
        meeting.completed = true;

        recordAudit("MEETING_COMPLETED", meetingId, organizerId);
    }

    // --------------------------------------------------------
    // DECISION RECORDING
    // --------------------------------------------------------

    string recordDecision(
        const string& meetingId,
        const string& ownerId,
        const string& description,
        bool approved
    ) {
        auto iterator = meetings.find(meetingId);

        if (iterator == meetings.end() || !iterator->second.completed) {
            throw StateTransitionError(
                "Decision requires completed meeting."
            );
        }

        getStakeholder(ownerId);
        validateText(description, "Decision description");

        string id = generateId("DEC");

        decisions.emplace(
            id,
            Decision{
                id,
                meetingId,
                description,
                ownerId,
                approved
            }
        );

        recordAudit("DECISION_RECORDED", id, ownerId);

        return id;
    }

    // --------------------------------------------------------
    // ACTION-ITEM MANAGEMENT
    // --------------------------------------------------------

    string createAction(
        const string& description,
        const string& assignedTo,
        const string& createdBy,
        TimePoint dueDate
    ) {
        getStakeholder(assignedTo);
        getStakeholder(createdBy);

        validateText(description, "Action description");

        string id = generateId("ACT");

        actions.emplace(
            id,
            ActionItem{
                id,
                description,
                assignedTo,
                createdBy,
                dueDate
            }
        );

        recordAudit("ACTION_CREATED", id, createdBy);

        return id;
    }

    void updateAction(
        const string& actionId,
        const string& actorId,
        ActionState nextState
    ) {
        auto iterator = actions.find(actionId);

        if (iterator == actions.end()) {
            throw NotFoundError("Action not found.");
        }

        ActionItem& action = iterator->second;

        if (actorId != action.assignedTo &&
            actorId != action.createdBy) {
            throw AuthorizationError("Actor cannot update action.");
        }

        map<ActionState, set<ActionState>> transitions = {
            {ActionState::Open, {
                ActionState::InProgress,
                ActionState::Blocked,
                ActionState::Cancelled
            }},
            {ActionState::InProgress, {
                ActionState::Completed,
                ActionState::Blocked,
                ActionState::Cancelled
            }},
            {ActionState::Blocked, {
                ActionState::InProgress,
                ActionState::Cancelled
            }},
            {ActionState::Completed, {}},
            {ActionState::Cancelled, {}}
        };

        if (!transitions[action.state].count(nextState)) {
            throw StateTransitionError("Invalid action transition.");
        }

        action.state = nextState;

        if (nextState == ActionState::Completed) {
            action.completed = true;
        }

        recordAudit("ACTION_UPDATED", actionId, actorId);
    }

    vector<ActionItem> overdueActions() const {
        vector<ActionItem> result;

        const TimePoint now = Clock::now();

        for (const auto& entry : actions) {
            const ActionItem& action = entry.second;

            if (action.dueDate < now &&
                action.state != ActionState::Completed &&
                action.state != ActionState::Cancelled) {
                result.push_back(action);
            }
        }

        return result;
    }

    // --------------------------------------------------------
    // COMMUNICATION REPORTING
    // --------------------------------------------------------

    void printMetrics() const {
        size_t expectedAcknowledgements = 0;
        size_t actualAcknowledgements = 0;
        size_t sentCount = 0;
        size_t escalatedCount = 0;

        for (const auto& entry : messages) {
            const Message& message = entry.second;

            if (message.hasBeenSent) {
                ++sentCount;
                expectedAcknowledgements += message.recipients.size();
                actualAcknowledgements += message.acknowledgements.size();
            }

            if (message.state == MessageState::Escalated) {
                ++escalatedCount;
            }
        }

        double acknowledgementRate = expectedAcknowledgements
            ? 100.0 * actualAcknowledgements / expectedAcknowledgements
            : 0.0;

        cout << "\nPROJECT COMMUNICATION REPORT\n"
             << "Project: " << projectName << '\n'
             << "Stakeholders: " << stakeholders.size() << '\n'
             << "Communication plans: " << plans.size() << '\n'
             << "Messages: " << messages.size() << '\n'
             << "Sent messages: " << sentCount << '\n'
             << "Escalated messages: " << escalatedCount << '\n'
             << "Acknowledgement rate: "
             << fixed << setprecision(2)
             << acknowledgementRate << "%\n"
             << "Meetings: " << meetings.size() << '\n'
             << "Decisions: " << decisions.size() << '\n'
             << "Actions: " << actions.size() << '\n'
             << "Overdue actions: " << overdueActions().size() << '\n'
             << "Audit events: " << audit.size() << '\n';
    }

    void printPendingAcknowledgements(const string& messageId) const {
        cout << "\nPENDING ACKNOWLEDGEMENTS\n";

        for (const string& recipient : getUnacknowledged(messageId)) {
            cout << recipient << '\n';
        }
    }

    void printAudit() const {
        cout << "\nAUDIT TRAIL\n";

        for (const AuditEvent& event : audit) {
            cout << formatTime(event.timestamp)
                 << " | " << event.type
                 << " | " << event.entityId
                 << " | " << event.actorId
                 << '\n';
        }
    }
};

// ============================================================
// MAIN SCENARIO
// ============================================================

int main() {

    try {

        ProjectCommunicationEngine engine(
            "Enterprise Project Management System"
        );

        Stakeholder manager{
            "ST-001",
            "Project Manager",
            "manager@example.com",
            Role::ProjectManager,
            5,
            5,
            Confidentiality::Restricted
        };

        Stakeholder sponsor{
            "ST-002",
            "Project Sponsor",
            "sponsor@example.com",
            Role::Sponsor,
            5,
            4,
            Confidentiality::Confidential
        };

        Stakeholder developer{
            "ST-003",
            "Development Lead",
            "developer@example.com",
            Role::Developer,
            3,
            5,
            Confidentiality::Internal
        };

        Stakeholder client{
            "ST-004",
            "Client Representative",
            "client@example.com",
            Role::Client,
            4,
            5,
            Confidentiality::Confidential
        };

        engine.addStakeholder(manager);
        engine.addStakeholder(sponsor);
        engine.addStakeholder(developer);
        engine.addStakeholder(client);

        engine.printStakeholders();

        TimePoint now = Clock::now();

        CommunicationPlan plan{
            "PLAN-001",
            sponsor.id,
            manager.id,
            Channel::Email,
            Purpose::StatusUpdate,
            "weekly",
            now + chrono::hours(24 * 7)
        };

        engine.addPlan(plan);

        string messageId = engine.createMessage(
            manager.id,
            "Weekly Project Status",
            "Development is 65 percent complete.",
            Channel::Email,
            Purpose::StatusUpdate,
            Confidentiality::Internal,
            {sponsor.id, developer.id}
        );

        engine.sendMessage(messageId);

        engine.acknowledgeMessage(messageId, sponsor.id);

        engine.printPendingAcknowledgements(messageId);

        engine.acknowledgeMessage(messageId, developer.id);

        string meetingId = engine.scheduleMeeting(
            manager.id,
            "Weekly Project Review",
            {sponsor.id, developer.id, client.id},
            {
                "Project progress",
                "Risk assessment",
                "Delivery schedule"
            },
            now + chrono::hours(24)
        );

        engine.completeMeeting(
            meetingId,
            manager.id,
            "Testing preparation approved. Delivery milestone unchanged."
        );

        engine.recordDecision(
            meetingId,
            sponsor.id,
            "Approve testing preparation.",
            true
        );

        string actionId = engine.createAction(
            "Prepare the software testing plan.",
            developer.id,
            manager.id,
            now + chrono::hours(24 * 5)
        );

        engine.updateAction(
            actionId,
            developer.id,
            ActionState::InProgress
        );

        engine.printMetrics();
        engine.printAudit();

        // Authorization failure test.
        try {
            engine.createMessage(
                developer.id,
                "Restricted executive update",
                "Unauthorized communication example.",
                Channel::Email,
                Purpose::Escalation,
                Confidentiality::Restricted,
                {sponsor.id}
            );
        } catch (const AuthorizationError& error) {
            cout << "\nAuthorization correctly rejected: "
                 << error.what() << '\n';
        }

        // Invalid state transition test.
        try {
            engine.updateAction(
                actionId,
                developer.id,
                ActionState::Open
            );
        } catch (const StateTransitionError& error) {
            cout << "Invalid transition correctly rejected: "
                 << error.what() << '\n';
        }

        cout << "\nAll communication governance checks completed.\n";

    } catch (const exception& error) {
        cerr << "Application error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
