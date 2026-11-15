#include <algorithm>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class Priority {
    LOW,
    MEDIUM,
    HIGH,
    CRITICAL
};

enum class Engagement {
    UNAWARE,
    RESISTANT,
    NEUTRAL,
    SUPPORTIVE,
    LEADING
};

enum class MessageStatus {
    DRAFT,
    APPROVED,
    SENT,
    ACKNOWLEDGED,
    ESCALATED,
    CANCELLED
};

enum class ReviewDecision {
    COMMENTED,
    APPROVED,
    CHANGES_REQUESTED,
    DISMISSED
};

enum class MergeLikeChannel {
    EMAIL,
    MEETING,
    REPORT,
    PHONE,
    COLLABORATION
};

string toString(Priority p) {
    switch (p) {
        case Priority::LOW: return "LOW";
        case Priority::MEDIUM: return "MEDIUM";
        case Priority::HIGH: return "HIGH";
        case Priority::CRITICAL: return "CRITICAL";
    }
    return "UNKNOWN";
}

string toString(MessageStatus s) {
    switch (s) {
        case MessageStatus::DRAFT: return "DRAFT";
        case MessageStatus::APPROVED: return "APPROVED";
        case MessageStatus::SENT: return "SENT";
        case MessageStatus::ACKNOWLEDGED: return "ACKNOWLEDGED";
        case MessageStatus::ESCALATED: return "ESCALATED";
        case MessageStatus::CANCELLED: return "CANCELLED";
    }
    return "UNKNOWN";
}

string toString(ReviewDecision d) {
    switch (d) {
        case ReviewDecision::COMMENTED: return "COMMENTED";
        case ReviewDecision::APPROVED: return "APPROVED";
        case ReviewDecision::CHANGES_REQUESTED:
            return "CHANGES_REQUESTED";
        case ReviewDecision::DISMISSED: return "DISMISSED";
    }
    return "UNKNOWN";
}

struct Stakeholder {
    string id;
    string name;
    string role;
    string department;
    string email;
    int influence;
    int interest;
    Engagement engagement;
    bool active = true;

    void validate() const {
        if (id.empty() || name.empty() || role.empty()) {
            throw invalid_argument("Required stakeholder fields are missing.");
        }

        if (email.find('@') == string::npos ||
            email.find('.') == string::npos) {
            throw invalid_argument("Invalid stakeholder email.");
        }

        if (influence < 1 || influence > 3 ||
            interest < 1 || interest > 3) {
            throw invalid_argument("Influence and interest must be 1-3.");
        }
    }

    string category() const {
        if (influence == 3 && interest == 3) {
            return "MANAGE_CLOSELY";
        }

        if (influence == 3) {
            return "KEEP_SATISFIED";
        }

        if (interest == 3) {
            return "KEEP_INFORMED";
        }

        return "MONITOR";
    }
};

struct Review {
    string reviewerId;
    ReviewDecision decision;
    string comment;
    bool eligible;
    chrono::system_clock::time_point submittedAt;
};

struct Communication {
    string id;
    string stakeholderId;
    string subject;
    string body;
    Priority priority;
    MergeLikeChannel channel;
    MessageStatus status = MessageStatus::DRAFT;

    bool approvalRequired = true;
    bool approvedByAuthorizedPerson = false;
    bool acknowledgementRequired = true;
    bool confidential = false;

    optional<chrono::system_clock::time_point> deadline;
    optional<chrono::system_clock::time_point> sentAt;
    optional<chrono::system_clock::time_point> acknowledgedAt;

    vector<Review> reviews;
};

struct GovernancePolicy {
    int requiredApprovals = 1;
    int acknowledgementHours = 48;
    bool requireResolvedDiscussions = true;
    bool requireAuthorizedApproval = true;
    bool permitConfidentialEmail = false;
    set<MergeLikeChannel> permittedChannels = {
        MergeLikeChannel::EMAIL,
        MergeLikeChannel::MEETING,
        MergeLikeChannel::REPORT
    };

    void validate() const {
        if (requiredApprovals < 0 || acknowledgementHours < 1) {
            throw invalid_argument("Invalid governance policy.");
        }
    }
};

class CommunicationEngine {
private:
    map<string, Stakeholder> stakeholders;
    map<string, Communication> communications;
    GovernancePolicy policy;

    vector<string> auditLog;

    void audit(const string& event, const string& id) {
        auditLog.push_back(event + " | " + id);
    }

    Stakeholder& getStakeholder(const string& id) {
        auto it = stakeholders.find(id);

        if (it == stakeholders.end()) {
            throw runtime_error("Stakeholder not found: " + id);
        }

        return it->second;
    }

    Communication& getCommunication(const string& id) {
        auto it = communications.find(id);

        if (it == communications.end()) {
            throw runtime_error("Communication not found: " + id);
        }

        return it->second;
    }

    int activeApprovals(const Communication& communication) const {
        set<string> uniqueReviewers;
        int count = 0;

        for (const auto& review : communication.reviews) {
            if (!review.eligible ||
                review.decision != ReviewDecision::APPROVED) {
                continue;
            }

            if (uniqueReviewers.insert(review.reviewerId).second) {
                ++count;
            }
        }

        return count;
    }

    bool discussionsResolved(const Communication& communication) const {
        return all_of(
            communication.reviews.begin(),
            communication.reviews.end(),
            [](const Review& review) {
                return review.decision != ReviewDecision::CHANGES_REQUESTED;
            }
        );
    }

public:
    explicit CommunicationEngine(GovernancePolicy governance)
        : policy(std::move(governance)) {
        policy.validate();
    }

    void addStakeholder(const Stakeholder& stakeholder) {
        stakeholder.validate();

        if (stakeholders.count(stakeholder.id)) {
            throw invalid_argument("Duplicate stakeholder ID.");
        }

        for (const auto& entry : stakeholders) {
            if (entry.second.email == stakeholder.email) {
                throw invalid_argument("Duplicate stakeholder email.");
            }
        }

        stakeholders.emplace(stakeholder.id, stakeholder);
        audit("STAKEHOLDER_CREATED", stakeholder.id);
    }

    void createCommunication(const Communication& communication) {
        Stakeholder& stakeholder = getStakeholder(
            communication.stakeholderId
        );

        if (!stakeholder.active) {
            throw runtime_error("Stakeholder is inactive.");
        }

        if (communication.id.empty() ||
            communication.subject.empty() ||
            communication.body.empty()) {
            throw invalid_argument("Communication fields cannot be empty.");
        }

        if (communications.count(communication.id)) {
            throw invalid_argument("Duplicate communication ID.");
        }

        if (!policy.permittedChannels.count(communication.channel)) {
            throw runtime_error("Communication channel is prohibited.");
        }

        if (communication.confidential &&
            communication.channel == MergeLikeChannel::EMAIL &&
            !policy.permitConfidentialEmail) {
            throw runtime_error("Confidential email is prohibited by policy.");
        }

        if (communication.deadline &&
            communication.deadline.value() <=
                chrono::system_clock::now()) {
            throw invalid_argument("Deadline must be in the future.");
        }

        communications.emplace(communication.id, communication);
        audit("COMMUNICATION_DRAFTED", communication.id);
    }

    void addReview(
        const string& communicationId,
        const string& reviewerId,
        ReviewDecision decision,
        const string& comment,
        bool eligible
    ) {
        Communication& communication = getCommunication(communicationId);
        Stakeholder& reviewer = getStakeholder(reviewerId);

        if (!reviewer.active || !eligible) {
            throw runtime_error("Reviewer is not eligible.");
        }

        if (reviewerId == communication.stakeholderId) {
            throw runtime_error("Sender cannot approve their own message.");
        }

        if (communication.status != MessageStatus::DRAFT) {
            throw runtime_error("Reviews are closed after draft state.");
        }

        if (decision == ReviewDecision::CHANGES_REQUESTED &&
            comment.empty()) {
            throw invalid_argument("Requested changes require a comment.");
        }

        if (decision == ReviewDecision::DISMISSED) {
            throw invalid_argument("New reviews cannot start dismissed.");
        }

        for (const auto& existing : communication.reviews) {
            if (existing.reviewerId == reviewerId &&
                existing.decision == ReviewDecision::APPROVED &&
                decision == ReviewDecision::APPROVED) {
                throw runtime_error("Reviewer has already approved.");
            }
        }

        communication.reviews.push_back({
            reviewerId,
            decision,
            comment,
            eligible,
            chrono::system_clock::now()
        });

        audit("REVIEW_" + toString(decision), communicationId);
    }

    bool approvalEligible(const Communication& communication) const {
        if (activeApprovals(communication) < policy.requiredApprovals) {
            return false;
        }

        if (policy.requireResolvedDiscussions &&
            !discussionsResolved(communication)) {
            return false;
        }

        return true;
    }

    void approve(const string& communicationId, bool authorized) {
        Communication& communication = getCommunication(communicationId);

        if (communication.status != MessageStatus::DRAFT) {
            throw runtime_error("Only drafts can be approved.");
        }

        if (!authorized && policy.requireAuthorizedApproval) {
            throw runtime_error("Approver lacks required authorization.");
        }

        if (!approvalEligible(communication)) {
            throw runtime_error("Approval requirements are not satisfied.");
        }

        communication.approvedByAuthorizedPerson = authorized;
        communication.status = MessageStatus::APPROVED;

        audit("COMMUNICATION_APPROVED", communicationId);
    }

    void send(const string& communicationId) {
        Communication& communication = getCommunication(communicationId);
        Stakeholder& stakeholder = getStakeholder(
            communication.stakeholderId
        );

        if (!stakeholder.active) {
            throw runtime_error("Recipient is inactive.");
        }

        if (communication.status != MessageStatus::APPROVED &&
            communication.approvalRequired) {
            throw runtime_error("Approval is required.");
        }

        if (communication.status != MessageStatus::APPROVED &&
            communication.status != MessageStatus::DRAFT) {
            throw runtime_error("Invalid communication state.");
        }

        communication.sentAt = chrono::system_clock::now();
        communication.status = MessageStatus::SENT;

        audit("COMMUNICATION_SENT", communicationId);
    }

    void acknowledge(
        const string& communicationId,
        const string& stakeholderId
    ) {
        Communication& communication = getCommunication(communicationId);

        if (communication.stakeholderId != stakeholderId) {
            throw runtime_error("Acknowledgement identity mismatch.");
        }

        if (communication.status != MessageStatus::SENT) {
            throw runtime_error("Only sent communications can be acknowledged.");
        }

        communication.acknowledgedAt = chrono::system_clock::now();
        communication.status = MessageStatus::ACKNOWLEDGED;

        audit("ACKNOWLEDGEMENT_RECEIVED", communicationId);
    }

    vector<string> escalateOverdue(
        chrono::system_clock::time_point now
    ) {
        vector<string> escalated;

        for (auto& entry : communications) {
            Communication& communication = entry.second;

            if (communication.status != MessageStatus::SENT ||
                !communication.deadline ||
                communication.deadline.value() >= now) {
                continue;
            }

            communication.status = MessageStatus::ESCALATED;
            escalated.push_back(communication.id);

            audit("COMMUNICATION_ESCALATED", communication.id);
        }

        return escalated;
    }

    void printDashboard() const {
        map<string, int> categories;
        map<string, int> statuses;

        int sent = 0;
        int acknowledged = 0;

        for (const auto& entry : stakeholders) {
            if (entry.second.active) {
                ++categories[entry.second.category()];
            }
        }

        for (const auto& entry : communications) {
            const auto& c = entry.second;

            ++statuses[toString(c.status)];

            if (c.sentAt) {
                ++sent;
            }

            if (c.acknowledgedAt) {
                ++acknowledged;
            }
        }

        cout << "\nSTAKEHOLDER DASHBOARD\n";
        cout << "Active stakeholders: ";

        int activeCount = 0;

        for (const auto& entry : stakeholders) {
            if (entry.second.active) ++activeCount;
        }

        cout << activeCount << "\n";

        cout << "\nPOWER-INTEREST DISTRIBUTION\n";

        for (const auto& entry : categories) {
            cout << entry.first << ": " << entry.second << "\n";
        }

        cout << "\nCOMMUNICATION STATUS\n";

        for (const auto& entry : statuses) {
            cout << entry.first << ": " << entry.second << "\n";
        }

        double rate = sent
            ? static_cast<double>(acknowledged) / sent * 100.0
            : 0.0;

        cout << fixed << setprecision(2);
        cout << "\nAcknowledgement rate: " << rate << "%\n";

        cout << "\nAUDIT EVENTS: " << auditLog.size() << "\n";
    }

    void printAudit() const {
        cout << "\nAUDIT LOG\n";

        for (const auto& event : auditLog) {
            cout << event << "\n";
        }
    }
};

int main() {
    try {
        GovernancePolicy policy;
        policy.requiredApprovals = 1;
        policy.acknowledgementHours = 24;

        CommunicationEngine engine(policy);

        Stakeholder sponsor{
            "STK-001",
            "Ananya Sharma",
            "Project Sponsor",
            "Executive Management",
            "ananya@example.com",
            3,
            3,
            Engagement::SUPPORTIVE,
            true
        };

        Stakeholder reviewer{
            "STK-002",
            "Rahul Verma",
            "Technical Lead",
            "Engineering",
            "rahul@example.com",
            3,
            3,
            Engagement::LEADING,
            true
        };

        Stakeholder user{
            "STK-003",
            "Priya Singh",
            "Operations Representative",
            "Operations",
            "priya@example.com",
            2,
            3,
            Engagement::NEUTRAL,
            true
        };

        engine.addStakeholder(sponsor);
        engine.addStakeholder(reviewer);
        engine.addStakeholder(user);

        Communication message;
        message.id = "COM-001";
        message.stakeholderId = "STK-001";
        message.subject = "Deployment Readiness and Project Status";
        message.body =
            "Integration testing is complete. "
            "Three issues require monitoring. "
            "Approval is requested for the deployment schedule.";
        message.priority = Priority::HIGH;
        message.channel = MergeLikeChannel::EMAIL;
        message.approvalRequired = true;
        message.acknowledgementRequired = true;
        message.deadline = chrono::system_clock::now() +
                           chrono::hours(24);

        engine.createCommunication(message);

        engine.addReview(
            "COM-001",
            "STK-002",
            ReviewDecision::APPROVED,
            "Technical content and delivery risks verified.",
            true
        );

        engine.approve("COM-001", true);
        engine.send("COM-001");
        engine.acknowledge("COM-001", "STK-001");

        engine.printDashboard();
        engine.printAudit();

        // A second message demonstrates overdue escalation.
        Communication overdue;
        overdue.id = "COM-002";
        overdue.stakeholderId = "STK-003";
        overdue.subject = "Operational Feedback Request";
        overdue.body = "Please confirm operational readiness.";
        overdue.priority = Priority::MEDIUM;
        overdue.channel = MergeLikeChannel::EMAIL;
        overdue.approvalRequired = false;
        overdue.deadline = chrono::system_clock::now() -
                           chrono::hours(2);

        engine.createCommunication(overdue);
        engine.send("COM-002");

        auto escalations = engine.escalateOverdue(
            chrono::system_clock::now()
        );

        cout << "\nESCALATED COMMUNICATIONS\n";

        for (const auto& id : escalations) {
            cout << id << "\n";
        }

        return 0;

    } catch (const exception& error) {
        cerr << "Workflow error: " << error.what() << "\n";
        return 1;
    }
}
