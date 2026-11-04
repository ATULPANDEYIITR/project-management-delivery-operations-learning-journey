#include <algorithm>
#include <chrono>
#include <cctype>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;
using Clock = chrono::system_clock;
using TimePoint = Clock::time_point;

enum class Role {
    Admin,
    Manager,
    Member,
    Observer
};

enum class ChannelType {
    General,
    Project,
    Announcement,
    Incident,
    Private
};

enum class Priority {
    Low = 1,
    Normal = 2,
    High = 3,
    Urgent = 4
};

enum class MessageState {
    Sent,
    Acknowledged,
    Resolved,
    Archived
};

enum class TaskState {
    Open,
    InProgress,
    Blocked,
    Completed
};

string toString(Role role) {
    switch (role) {
        case Role::Admin: return "Admin";
        case Role::Manager: return "Manager";
        case Role::Member: return "Member";
        case Role::Observer: return "Observer";
    }
    throw logic_error("Unknown role.");
}

string toString(Priority priority) {
    switch (priority) {
        case Priority::Low: return "LOW";
        case Priority::Normal: return "NORMAL";
        case Priority::High: return "HIGH";
        case Priority::Urgent: return "URGENT";
    }
    throw logic_error("Unknown priority.");
}

string toString(TaskState state) {
    switch (state) {
        case TaskState::Open: return "OPEN";
        case TaskState::InProgress: return "IN_PROGRESS";
        case TaskState::Blocked: return "BLOCKED";
        case TaskState::Completed: return "COMPLETED";
    }
    throw logic_error("Unknown task state.");
}

string trim(const string& input) {
    const auto first = input.find_first_not_of(" \t\n\r");

    if (first == string::npos) {
        return "";
    }

    const auto last = input.find_last_not_of(" \t\n\r");
    return input.substr(first, last - first + 1);
}

struct User {
    int id;
    string name;
    string email;
    Role role;
    bool active = true;
};

struct Channel {
    int id;
    string name;
    ChannelType type;
    int createdBy;
    set<int> members;
    bool archived = false;
};

struct Message {
    int id;
    int channelId;
    int senderId;
    string content;
    Priority priority;
    TimePoint createdAt;
    MessageState state = MessageState::Sent;
    optional<int> parentId;
    set<int> recipients;
    set<int> readBy;
    set<int> acknowledgedBy;
};

struct ActionItem {
    int id;
    int messageId;
    int ownerId;
    string title;
    TimePoint dueAt;
    TaskState state = TaskState::Open;
};

struct Escalation {
    int messageId;
    Priority priority;
    vector<int> pendingUsers;
    long ageMinutes;
};

class GovernanceEngine {
private:
    unordered_map<int, User> users;
    unordered_map<int, Channel> channels;
    unordered_map<int, Message> messages;
    unordered_map<int, ActionItem> tasks;

    vector<string> auditLog;

    int nextUserId = 1;
    int nextChannelId = 1;
    int nextMessageId = 1;
    int nextTaskId = 1;

    void audit(int actor, const string& event, int target) {
        auditLog.push_back(
            "actor=" + to_string(actor) +
            " event=" + event +
            " target=" + to_string(target)
        );
    }

    const User& requireUser(int id) const {
        auto it = users.find(id);

        if (it == users.end() || !it->second.active) {
            throw runtime_error("User unavailable.");
        }

        return it->second;
    }

    Channel& requireMembership(int userId, int channelId) {
        requireUser(userId);

        auto it = channels.find(channelId);

        if (it == channels.end() || it->second.archived) {
            throw runtime_error("Channel unavailable.");
        }

        if (!it->second.members.count(userId)) {
            throw runtime_error("Channel membership required.");
        }

        return it->second;
    }

    const Message& requireMessage(int messageId) const {
        auto it = messages.find(messageId);

        if (it == messages.end()) {
            throw runtime_error("Message not found.");
        }

        return it->second;
    }

    static bool validTransition(TaskState from, TaskState to) {
        switch (from) {
            case TaskState::Open:
                return to == TaskState::InProgress ||
                       to == TaskState::Blocked ||
                       to == TaskState::Completed;

            case TaskState::InProgress:
                return to == TaskState::Open ||
                       to == TaskState::Blocked ||
                       to == TaskState::Completed;

            case TaskState::Blocked:
                return to == TaskState::Open ||
                       to == TaskState::InProgress;

            case TaskState::Completed:
                return false;
        }

        return false;
    }

public:
    int registerUser(
        const string& name,
        const string& email,
        Role role
    ) {
        if (trim(name).empty() || name.size() > 100) {
            throw invalid_argument("Invalid user name.");
        }

        if (email.find('@') == string::npos ||
            email.find('.') == string::npos) {
            throw invalid_argument("Invalid email.");
        }

        for (const auto& entry : users) {
            if (entry.second.email == email) {
                throw invalid_argument("Duplicate email.");
            }
        }

        int id = nextUserId++;

        users.emplace(id, User{
            id, trim(name), email, role, true
        });

        audit(id, "USER_REGISTERED", id);
        return id;
    }

    int createChannel(
        int creatorId,
        const string& name,
        ChannelType type,
        const set<int>& requestedMembers
    ) {
        const User& creator = requireUser(creatorId);

        if (creator.role != Role::Admin &&
            creator.role != Role::Manager) {
            throw runtime_error("Channel creation denied.");
        }

        if (trim(name).empty() || name.size() > 80) {
            throw invalid_argument("Invalid channel name.");
        }

        set<int> members = requestedMembers;
        members.insert(creatorId);

        for (int id : members) {
            requireUser(id);
        }

        if (type == ChannelType::Private && members.size() < 2) {
            throw invalid_argument(
                "Private channel needs multiple members."
            );
        }

        int id = nextChannelId++;

        channels.emplace(id, Channel{
            id, trim(name), type, creatorId, members, false
        });

        audit(creatorId, "CHANNEL_CREATED", id);
        return id;
    }

    void addMember(int actorId, int channelId, int memberId) {
        Channel& channel = requireMembership(actorId, channelId);
        const User& actor = requireUser(actorId);
        requireUser(memberId);

        if (actor.role != Role::Admin &&
            actor.role != Role::Manager) {
            throw runtime_error("Member management denied.");
        }

        channel.members.insert(memberId);
        audit(actorId, "MEMBER_ADDED", channelId);
    }

    int sendMessage(
        int senderId,
        int channelId,
        const string& content,
        Priority priority,
        optional<set<int>> requestedRecipients = nullopt,
        optional<int> parentId = nullopt
    ) {
        Channel& channel = requireMembership(senderId, channelId);
        const User& sender = requireUser(senderId);

        if (sender.role == Role::Observer) {
            throw runtime_error("Observers cannot send messages.");
        }

        if (channel.type == ChannelType::Announcement &&
            sender.role != Role::Admin &&
            sender.role != Role::Manager) {
            throw runtime_error("Announcement permission denied.");
        }

        string cleaned = trim(content);

        if (cleaned.empty() || cleaned.size() > 10000) {
            throw invalid_argument("Invalid message content.");
        }

        if (static_cast<int>(priority) < 1 ||
            static_cast<int>(priority) > 4) {
            throw invalid_argument("Invalid priority.");
        }

        if (parentId.has_value()) {
            const Message& parent = requireMessage(*parentId);

            if (parent.channelId != channelId) {
                throw invalid_argument(
                    "Reply must belong to the same channel."
                );
            }
        }

        set<int> recipients;

        if (requestedRecipients.has_value()) {
            recipients = *requestedRecipients;
        } else {
            recipients = channel.members;
            recipients.erase(senderId);
        }

        for (int id : recipients) {
            requireUser(id);

            if (!channel.members.count(id)) {
                throw runtime_error("Recipient is not a channel member.");
            }
        }

        int id = nextMessageId++;

        messages.emplace(id, Message{
            id,
            channelId,
            senderId,
            cleaned,
            priority,
            Clock::now(),
            MessageState::Sent,
            parentId,
            recipients,
            {},
            {}
        });

        audit(senderId, "MESSAGE_SENT", id);
        return id;
    }

    void markRead(int userId, int messageId) {
        const Message& existing = requireMessage(messageId);

        requireMembership(userId, existing.channelId);

        if (userId != existing.senderId &&
            !existing.recipients.count(userId)) {
            throw runtime_error("Message access denied.");
        }

        messages.at(messageId).readBy.insert(userId);
        audit(userId, "MESSAGE_READ", messageId);
    }

    void acknowledge(int userId, int messageId) {
        markRead(userId, messageId);

        Message& message = messages.at(messageId);

        if (!message.recipients.count(userId)) {
            throw runtime_error("Recipient acknowledgment required.");
        }

        message.acknowledgedBy.insert(userId);

        bool complete = all_of(
            message.recipients.begin(),
            message.recipients.end(),
            [&](int recipient) {
                return message.acknowledgedBy.count(recipient) > 0;
            }
        );

        if (complete) {
            message.state = MessageState::Acknowledged;
        }

        audit(userId, "MESSAGE_ACKNOWLEDGED", messageId);
    }

    int createTask(
        int creatorId,
        int messageId,
        int ownerId,
        const string& title,
        TimePoint dueAt
    ) {
        const Message& message = requireMessage(messageId);

        requireMembership(creatorId, message.channelId);
        requireMembership(ownerId, message.channelId);

        const User& creator = requireUser(creatorId);

        if (creatorId != message.senderId &&
            creator.role != Role::Admin &&
            creator.role != Role::Manager) {
            throw runtime_error("Task assignment denied.");
        }

        if (trim(title).empty() || dueAt <= Clock::now()) {
            throw invalid_argument("Invalid task details.");
        }

        int id = nextTaskId++;

        tasks.emplace(id, ActionItem{
            id,
            messageId,
            ownerId,
            trim(title),
            dueAt,
            TaskState::Open
        });

        audit(creatorId, "TASK_CREATED", id);
        return id;
    }

    void updateTask(
        int actorId,
        int taskId,
        TaskState nextState
    ) {
        requireUser(actorId);

        auto it = tasks.find(taskId);

        if (it == tasks.end()) {
            throw runtime_error("Task not found.");
        }

        ActionItem& task = it->second;
        const Message& message = requireMessage(task.messageId);
        const User& actor = requireUser(actorId);

        if (actorId != task.ownerId &&
            actorId != message.senderId &&
            actor.role != Role::Admin &&
            actor.role != Role::Manager) {
            throw runtime_error("Task update denied.");
        }

        if (task.state != nextState &&
            !validTransition(task.state, nextState)) {
            throw runtime_error("Invalid task state transition.");
        }

        task.state = nextState;
        audit(actorId, "TASK_UPDATED", taskId);
    }

    vector<Escalation> getEscalations(
        TimePoint now = Clock::now()
    ) const {
        vector<Escalation> result;

        for (const auto& entry : messages) {
            const Message& message = entry.second;

            if (message.priority != Priority::High &&
                message.priority != Priority::Urgent) {
                continue;
            }

            if (message.state == MessageState::Resolved ||
                message.state == MessageState::Archived) {
                continue;
            }

            auto age = chrono::duration_cast<chrono::minutes>(
                now - message.createdAt
            ).count();

            long threshold = message.priority == Priority::Urgent
                ? 15
                : 240;

            vector<int> pending;

            for (int recipient : message.recipients) {
                if (!message.acknowledgedBy.count(recipient)) {
                    pending.push_back(recipient);
                }
            }

            if (age > threshold && !pending.empty()) {
                result.push_back({
                    message.id,
                    message.priority,
                    pending,
                    age
                });
            }
        }

        return result;
    }

    void printReport(int viewerId, int channelId) {
        Channel& channel = requireMembership(viewerId, channelId);

        int total = 0;
        int acknowledged = 0;
        int unread = 0;

        for (const auto& entry : messages) {
            const Message& message = entry.second;

            if (message.channelId != channelId) {
                continue;
            }

            ++total;

            if (message.state == MessageState::Acknowledged) {
                ++acknowledged;
            }

            if (message.recipients.count(viewerId) &&
                !message.readBy.count(viewerId)) {
                ++unread;
            }
        }

        cout << "\nCHANNEL REPORT\n";
        cout << "Channel: " << channel.name << '\n';
        cout << "Messages: " << total << '\n';
        cout << "Acknowledged: " << acknowledged << '\n';
        cout << "Pending: " << total - acknowledged << '\n';
        cout << "Unread for viewer: " << unread << '\n';

        int channelTasks = 0;
        int completedTasks = 0;

        for (const auto& entry : tasks) {
            const ActionItem& task = entry.second;
            const Message& source = messages.at(task.messageId);

            if (source.channelId == channelId) {
                ++channelTasks;

                if (task.state == TaskState::Completed) {
                    ++completedTasks;
                }
            }
        }

        cout << "Action items: " << channelTasks << '\n';
        cout << "Completed action items: " << completedTasks << '\n';
    }

    void printAudit() const {
        cout << "\nAUDIT EVENTS: " << auditLog.size() << '\n';

        for (const auto& event : auditLog) {
            cout << event << '\n';
        }
    }
};

int main() {
    try {
        GovernanceEngine system;

        int manager = system.registerUser(
            "Project Manager",
            "manager@example.com",
            Role::Manager
        );

        int developer = system.registerUser(
            "Developer",
            "developer@example.com",
            Role::Member
        );

        int tester = system.registerUser(
            "Tester",
            "tester@example.com",
            Role::Member
        );

        int observer = system.registerUser(
            "Observer",
            "observer@example.com",
            Role::Observer
        );

        int channel = system.createChannel(
            manager,
            "Platform Delivery",
            ChannelType::Project,
            {developer, tester}
        );

        int message = system.sendMessage(
            manager,
            channel,
            "Finish integration testing and report deployment blockers.",
            Priority::High
        );

        system.markRead(developer, message);
        system.acknowledge(developer, message);
        system.acknowledge(tester, message);

        int task = system.createTask(
            manager,
            message,
            developer,
            "Complete integration tests",
            Clock::now() + chrono::hours(24)
        );

        system.updateTask(
            developer,
            task,
            TaskState::InProgress
        );

        system.printReport(manager, channel);

        auto escalations = system.getEscalations();

        cout << "\nESCALATIONS: " << escalations.size() << '\n';

        for (const auto& item : escalations) {
            cout << "Message " << item.messageId
                 << " priority " << toString(item.priority)
                 << " age " << item.ageMinutes << " minutes"
                 << " pending recipients "
                 << item.pendingUsers.size() << '\n';
        }

        try {
            system.sendMessage(
                observer,
                channel,
                "Unauthorized message",
                Priority::Normal
            );
        } catch (const exception& error) {
            cout << "\nExpected permission failure: "
                 << error.what() << '\n';
        }

        try {
            system.updateTask(
                developer,
                task,
                TaskState::Blocked
            );

            system.updateTask(
                developer,
                task,
                TaskState::InProgress
            );

            system.updateTask(
                developer,
                task,
                TaskState::Completed
            );

            system.updateTask(
                developer,
                task,
                TaskState::InProgress
            );
        } catch (const exception& error) {
            cout << "Expected state failure: "
                 << error.what() << '\n';
        }

        system.printAudit();

        cout << "\nCommunication governance simulation completed.\n";

    } catch (const exception& error) {
        cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
