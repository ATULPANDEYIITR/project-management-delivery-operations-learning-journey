#include <algorithm>
#include <cmath>
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

enum class Channel {
    Email,
    Meeting,
    Report,
    Newsletter,
    Website,
    Workshop,
    Phone,
    SocialMedia
};

enum class Priority {
    Low,
    Medium,
    High,
    Critical
};

enum class ActivityStatus {
    Planned,
    Approved,
    Scheduled,
    InProgress,
    Sent,
    Completed,
    Failed,
    Cancelled
};

enum class ObjectiveStatus {
    Draft,
    Active,
    Completed,
    Cancelled
};

string toString(Channel channel) {
    switch (channel) {
        case Channel::Email: return "Email";
        case Channel::Meeting: return "Meeting";
        case Channel::Report: return "Report";
        case Channel::Newsletter: return "Newsletter";
        case Channel::Website: return "Website";
        case Channel::Workshop: return "Workshop";
        case Channel::Phone: return "Phone";
        case Channel::SocialMedia: return "Social Media";
    }

    throw runtime_error("Unknown channel.");
}

string toString(ActivityStatus status) {
    switch (status) {
        case ActivityStatus::Planned: return "Planned";
        case ActivityStatus::Approved: return "Approved";
        case ActivityStatus::Scheduled: return "Scheduled";
        case ActivityStatus::InProgress: return "In Progress";
        case ActivityStatus::Sent: return "Sent";
        case ActivityStatus::Completed: return "Completed";
        case ActivityStatus::Failed: return "Failed";
        case ActivityStatus::Cancelled: return "Cancelled";
    }

    throw runtime_error("Unknown activity status.");
}

struct Stakeholder {
    string name;
    string audience;
    string department;
    int influence;
    int interest;
    vector<Channel> preferredChannels;

    Stakeholder(
        string name,
        string audience,
        string department,
        int influence,
        int interest,
        vector<Channel> channels = {}
    ) :
        name(move(name)),
        audience(move(audience)),
        department(move(department)),
        influence(influence),
        interest(interest),
        preferredChannels(move(channels))
    {
        if (this->name.empty()) {
            throw invalid_argument("Stakeholder name is required.");
        }

        if (influence < 1 || influence > 5 ||
            interest < 1 || interest > 5) {
            throw invalid_argument("Influence and interest must be 1 to 5.");
        }
    }
};

struct Objective {
    int id;
    string title;
    string description;
    string desiredOutcome;
    vector<string> audiences;
    time_t deadline;
    Priority priority;
    ObjectiveStatus status;
};

struct ReviewFeedback {
    string respondent;
    int satisfaction;
    int understanding;
    string comments;
};

struct CommunicationActivity {
    int id;
    int objectiveId;
    string title;
    string message;
    Channel channel;
    vector<string> audience;
    string owner;
    time_t scheduledAt;
    double cost;
    bool approvalRequired;
    string approvedBy;
    ActivityStatus status;
    vector<ReviewFeedback> feedback;
};

struct Policy {
    double budget;
    bool requireApprovalForExternalCommunication;
    bool requireApprovalForCriticalCommunication;
    bool restrictWeekendActivities;
    size_t maximumActivities;
};

struct Evaluation {
    size_t total = 0;
    size_t completed = 0;
    size_t failed = 0;
    double committedCost = 0;
    double satisfaction = 0;
    double understanding = 0;
    size_t feedbackCount = 0;
};

class CommunicationGovernanceEngine {
private:
    Policy policy;

    map<int, Stakeholder> stakeholders;
    map<int, Objective> objectives;
    map<int, CommunicationActivity> activities;

    int nextStakeholderId = 1;
    int nextObjectiveId = 1;
    int nextActivityId = 1;

    double committedCost() const {
        double total = 0;

        for (const auto& [id, activity] : activities) {
            if (activity.status != ActivityStatus::Cancelled) {
                total += activity.cost;
            }
        }

        return total;
    }

    Objective& getObjective(int id) {
        auto it = objectives.find(id);

        if (it == objectives.end()) {
            throw invalid_argument("Objective does not exist.");
        }

        return it->second;
    }

    CommunicationActivity& getActivity(int id) {
        auto it = activities.find(id);

        if (it == activities.end()) {
            throw invalid_argument("Activity does not exist.");
        }

        return it->second;
    }

    void transition(
        CommunicationActivity& activity,
        ActivityStatus next
    ) {
        map<ActivityStatus, set<ActivityStatus>> allowed = {
            {
                ActivityStatus::Planned,
                {
                    ActivityStatus::Approved,
                    ActivityStatus::Cancelled
                }
            },
            {
                ActivityStatus::Approved,
                {
                    ActivityStatus::Scheduled,
                    ActivityStatus::Cancelled
                }
            },
            {
                ActivityStatus::Scheduled,
                {
                    ActivityStatus::InProgress,
                    ActivityStatus::Cancelled
                }
            },
            {
                ActivityStatus::InProgress,
                {
                    ActivityStatus::Sent,
                    ActivityStatus::Completed,
                    ActivityStatus::Failed
                }
            },
            {
                ActivityStatus::Sent,
                {
                    ActivityStatus::Completed,
                    ActivityStatus::Failed
                }
            },
            {
                ActivityStatus::Failed,
                {
                    ActivityStatus::Scheduled,
                    ActivityStatus::Cancelled
                }
            }
        };

        if (!allowed[activity.status].count(next)) {
            throw logic_error("Invalid activity state transition.");
        }

        activity.status = next;
    }

    static bool isWeekend(time_t timestamp) {
        tm localTime{};

#ifdef _WIN32
        localtime_s(&localTime, &timestamp);
#else
        localtime_r(&timestamp, &localTime);
#endif

        return localTime.tm_wday == 0 || localTime.tm_wday == 6;
    }

public:
    explicit CommunicationGovernanceEngine(Policy policy)
        : policy(move(policy))
    {
        if (this->policy.budget < 0) {
            throw invalid_argument("Budget cannot be negative.");
        }

        if (this->policy.maximumActivities == 0) {
            throw invalid_argument("Maximum activities must be positive.");
        }
    }

    int addStakeholder(Stakeholder stakeholder) {
        for (const auto& [id, existing] : stakeholders) {
            if (existing.name == stakeholder.name) {
                throw invalid_argument("Duplicate stakeholder.");
            }
        }

        int id = nextStakeholderId++;
        stakeholders.emplace(id, move(stakeholder));

        return id;
    }

    int addObjective(
        string title,
        string description,
        string outcome,
        vector<string> audiences,
        time_t deadline,
        Priority priority
    ) {
        if (title.empty() || description.empty() || outcome.empty()) {
            throw invalid_argument("Objective fields cannot be empty.");
        }

        if (audiences.empty()) {
            throw invalid_argument("Objective requires an audience.");
        }

        int id = nextObjectiveId++;

        objectives.emplace(
            id,
            Objective{
                id,
                move(title),
                move(description),
                move(outcome),
                move(audiences),
                deadline,
                priority,
                ObjectiveStatus::Draft
            }
        );

        return id;
    }

    void activateObjective(int id) {
        Objective& objective = getObjective(id);

        if (objective.status != ObjectiveStatus::Draft) {
            throw logic_error("Only draft objectives can be activated.");
        }

        objective.status = ObjectiveStatus::Active;
    }

    int scheduleActivity(
        int objectiveId,
        string title,
        string message,
        Channel channel,
        vector<string> audience,
        string owner,
        time_t scheduledAt,
        double cost,
        bool approvalRequired
    ) {
        Objective& objective = getObjective(objectiveId);

        if (objective.status != ObjectiveStatus::Active) {
            throw logic_error("Objective must be active.");
        }

        if (title.empty() || message.empty() || owner.empty()) {
            throw invalid_argument("Activity fields cannot be empty.");
        }

        if (audience.empty()) {
            throw invalid_argument("Activity requires an audience.");
        }

        if (scheduledAt > objective.deadline) {
            throw invalid_argument("Activity exceeds objective deadline.");
        }

        if (cost < 0 || cost > policy.budget - committedCost()) {
            throw invalid_argument("Insufficient budget or invalid cost.");
        }

        if (activities.size() >= policy.maximumActivities) {
            throw logic_error("Activity capacity reached.");
        }

        for (const string& name : audience) {
            bool found = false;

            for (const auto& [id, stakeholder] : stakeholders) {
                if (stakeholder.name == name) {
                    found = true;
                    break;
                }
            }

            if (!found) {
                throw invalid_argument("Unknown audience: " + name);
            }
        }

        if (policy.restrictWeekendActivities && isWeekend(scheduledAt)) {
            throw invalid_argument("Weekend communication is restricted.");
        }

        bool external = find(
            audience.begin(),
            audience.end(),
            "External Partners"
        ) != audience.end();

        if (policy.requireApprovalForExternalCommunication && external) {
            approvalRequired = true;
        }

        if (policy.requireApprovalForCriticalCommunication &&
            objective.priority == Priority::Critical) {
            approvalRequired = true;
        }

        int id = nextActivityId++;

        CommunicationActivity activity{
            id,
            objectiveId,
            move(title),
            move(message),
            channel,
            move(audience),
            move(owner),
            scheduledAt,
            cost,
            approvalRequired,
            "",
            approvalRequired
                ? ActivityStatus::Planned
                : ActivityStatus::Scheduled,
            {}
        };

        activities.emplace(id, move(activity));

        return id;
    }

    void approveActivity(int id, const string& approver) {
        CommunicationActivity& activity = getActivity(id);

        if (approver.empty()) {
            throw invalid_argument("Approver is required.");
        }

        if (activity.status != ActivityStatus::Planned) {
            throw logic_error("Activity is not awaiting approval.");
        }

        activity.approvedBy = approver;

        transition(activity, ActivityStatus::Approved);
        transition(activity, ActivityStatus::Scheduled);
    }

    void startActivity(int id) {
        CommunicationActivity& activity = getActivity(id);

        transition(activity, ActivityStatus::InProgress);
    }

    void recordDelivery(int id, bool success) {
        CommunicationActivity& activity = getActivity(id);

        if (success) {
            transition(activity, ActivityStatus::Sent);
        } else {
            transition(activity, ActivityStatus::Failed);
        }
    }

    void retryActivity(int id) {
        CommunicationActivity& activity = getActivity(id);

        transition(activity, ActivityStatus::Scheduled);
    }

    void completeActivity(int id) {
        CommunicationActivity& activity = getActivity(id);

        transition(activity, ActivityStatus::Completed);
    }

    void cancelActivity(int id) {
        CommunicationActivity& activity = getActivity(id);

        transition(activity, ActivityStatus::Cancelled);
    }

    void addFeedback(
        int activityId,
        string respondent,
        int satisfaction,
        int understanding,
        string comments
    ) {
        CommunicationActivity& activity = getActivity(activityId);

        if (satisfaction < 1 || satisfaction > 5 ||
            understanding < 1 || understanding > 5) {
            throw invalid_argument("Feedback scores must be 1 to 5.");
        }

        activity.feedback.push_back({
            move(respondent),
            satisfaction,
            understanding,
            move(comments)
        });
    }

    map<string, vector<string>> stakeholderMatrix() const {
        map<string, vector<string>> matrix = {
            {"Manage closely", {}},
            {"Keep satisfied", {}},
            {"Keep informed", {}},
            {"Monitor", {}}
        };

        for (const auto& [id, stakeholder] : stakeholders) {
            if (stakeholder.influence >= 4 && stakeholder.interest >= 4) {
                matrix["Manage closely"].push_back(stakeholder.name);
            } else if (stakeholder.influence >= 4) {
                matrix["Keep satisfied"].push_back(stakeholder.name);
            } else if (stakeholder.interest >= 4) {
                matrix["Keep informed"].push_back(stakeholder.name);
            } else {
                matrix["Monitor"].push_back(stakeholder.name);
            }
        }

        return matrix;
    }

    Channel recommendChannel(const string& stakeholderName) const {
        for (const auto& [id, stakeholder] : stakeholders) {
            if (stakeholder.name == stakeholderName) {
                if (!stakeholder.preferredChannels.empty()) {
                    return stakeholder.preferredChannels.front();
                }

                if (stakeholder.audience == "management") {
                    return Channel::Report;
                }

                if (stakeholder.audience == "technical") {
                    return Channel::Workshop;
                }

                if (stakeholder.audience == "public") {
                    return Channel::Website;
                }

                return Channel::Email;
            }
        }

        throw invalid_argument("Stakeholder not found.");
    }

    Evaluation evaluate() const {
        Evaluation result;

        result.total = activities.size();

        for (const auto& [id, activity] : activities) {
            if (activity.status == ActivityStatus::Completed) {
                result.completed++;
            }

            if (activity.status == ActivityStatus::Failed) {
                result.failed++;
            }

            if (activity.status != ActivityStatus::Cancelled) {
                result.committedCost += activity.cost;
            }

            for (const auto& feedback : activity.feedback) {
                result.satisfaction += feedback.satisfaction;
                result.understanding += feedback.understanding;
                result.feedbackCount++;
            }
        }

        if (result.feedbackCount > 0) {
            result.satisfaction /= result.feedbackCount;
            result.understanding /= result.feedbackCount;
        }

        return result;
    }

    void printReport() const {
        cout << "\nCOMMUNICATION PLANNING REPORT\n";
        cout << string(55, '=') << '\n';

        cout << "\nSTAKEHOLDER MATRIX\n";

        for (const auto& [category, names] : stakeholderMatrix()) {
            cout << category << ": ";

            for (const auto& name : names) {
                cout << name << "; ";
            }

            cout << '\n';
        }

        cout << "\nCOMMUNICATION ACTIVITIES\n";

        for (const auto& [id, activity] : activities) {
            cout << id << " | "
                 << activity.title << " | "
                 << toString(activity.channel) << " | "
                 << toString(activity.status) << " | "
                 << activity.cost << '\n';
        }

        Evaluation report = evaluate();

        cout << "\nPERFORMANCE\n";
        cout << "Total activities: " << report.total << '\n';
        cout << "Completed: " << report.completed << '\n';
        cout << "Failed: " << report.failed << '\n';
        cout << "Committed cost: " << report.committedCost << '\n';
        cout << "Remaining budget: "
             << policy.budget - report.committedCost << '\n';
        cout << "Average satisfaction: "
             << report.satisfaction << '\n';
        cout << "Average understanding: "
             << report.understanding << '\n';
    }
};

int main() {
    try {
        Policy policy{
            100000,
            true,
            true,
            false,
            100
        };

        CommunicationGovernanceEngine engine(policy);

        engine.addStakeholder({
            "Executive Management",
            "management",
            "Administration",
            5,
            5,
            {Channel::Report, Channel::Meeting}
        });

        engine.addStakeholder({
            "Technical Team",
            "technical",
            "Technology",
            3,
            5,
            {Channel::Workshop}
        });

        engine.addStakeholder({
            "Employees",
            "internal",
            "Operations",
            2,
            4,
            {Channel::Email}
        });

        engine.addStakeholder({
            "External Partners",
            "external",
            "Partnerships",
            4,
            2,
            {Channel::Email}
        });

        time_t now = time(nullptr);
        time_t deadline = now + 30 * 24 * 60 * 60;

        int objectiveId = engine.addObjective(
            "Digital Transformation",
            "Coordinate organizational communication.",
            "Improve awareness and stakeholder participation.",
            {
                "Executive Management",
                "Technical Team",
                "Employees",
                "External Partners"
            },
            deadline,
            Priority::High
        );

        engine.activateObjective(objectiveId);

        int briefingId = engine.scheduleActivity(
            objectiveId,
            "Management briefing",
            "Present transformation milestones and risks.",
            Channel::Meeting,
            {"Executive Management"},
            "Project Director",
            now + 2 * 24 * 60 * 60,
            15000,
            true
        );

        int workshopId = engine.scheduleActivity(
            objectiveId,
            "Technical workshop",
            "Discuss architecture and implementation responsibilities.",
            Channel::Workshop,
            {"Technical Team"},
            "Technical Lead",
            now + 5 * 24 * 60 * 60,
            25000,
            false
        );

        int partnerId = engine.scheduleActivity(
            objectiveId,
            "Partner notification",
            "Communicate operational changes.",
            Channel::Email,
            {"External Partners"},
            "Partnership Manager",
            now + 10 * 24 * 60 * 60,
            2000,
            false
        );

        engine.approveActivity(briefingId, "Chief Operating Officer");
        engine.startActivity(briefingId);
        engine.recordDelivery(briefingId, true);
        engine.completeActivity(briefingId);

        engine.startActivity(workshopId);
        engine.recordDelivery(workshopId, true);
        engine.completeActivity(workshopId);

        engine.approveActivity(partnerId, "Partnership Director");
        engine.startActivity(partnerId);
        engine.recordDelivery(partnerId, true);
        engine.completeActivity(partnerId);

        engine.addFeedback(
            workshopId,
            "Technical Team Lead",
            5,
            4,
            "The workshop clarified technical responsibilities."
        );

        engine.addFeedback(
            briefingId,
            "Executive Sponsor",
            5,
            5,
            "The objectives and milestones were clear."
        );

        engine.printReport();

        cout << "\nCHANNEL RECOMMENDATION\n";

        cout << "Technical Team: "
             << toString(engine.recommendChannel("Technical Team"))
             << '\n';

        cout << "\nExecution completed successfully.\n";

    } catch (const exception& error) {
        cerr << "Communication planning error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
