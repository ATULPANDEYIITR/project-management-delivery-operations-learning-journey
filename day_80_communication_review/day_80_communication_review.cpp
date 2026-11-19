#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class CommunicationType {
    Email,
    Meeting,
    Report,
    Presentation,
    Notice
};

enum class Status {
    Draft,
    Submitted,
    UnderReview,
    RevisionRequired,
    Rejected,
    Approved,
    Published,
    Archived
};

enum class Decision {
    Approve,
    Revise,
    Reject
};

enum class Severity {
    Low,
    Medium,
    High,
    Critical
};

string toString(Status status) {
    switch (status) {
        case Status::Draft: return "Draft";
        case Status::Submitted: return "Submitted";
        case Status::UnderReview: return "Under Review";
        case Status::RevisionRequired: return "Revision Required";
        case Status::Rejected: return "Rejected";
        case Status::Approved: return "Approved";
        case Status::Published: return "Published";
        case Status::Archived: return "Archived";
    }
    return "Unknown";
}

string toString(Decision decision) {
    switch (decision) {
        case Decision::Approve: return "Approve";
        case Decision::Revise: return "Revise";
        case Decision::Reject: return "Reject";
    }
    return "Unknown";
}

struct Stakeholder {
    string id;
    string name;
    string role;
    string department;
    bool active = true;
};

struct Communication {
    int id;
    string title;
    string subject;
    string content;
    string senderId;
    vector<string> recipients;
    vector<string> objectives;
    CommunicationType type;
    Status status = Status::Draft;
    int version = 1;
    bool acknowledgementRequired = false;
    int delivered = 0;
    int read = 0;
    int acknowledged = 0;
};

struct Review {
    int communicationId;
    string reviewerId;
    Decision decision;
    double score;
    int version;
    string feedback;
};

struct ReviewComment {
    int communicationId;
    string reviewerId;
    string criterion;
    string message;
    Severity severity;
    bool resolved = false;
};

struct BranchPolicy {
    int requiredApprovals = 2;
    double minimumScore = 70.0;
    double minimumDeliveryRate = 95.0;
    double minimumAcknowledgementRate = 80.0;
    bool blockCriticalComments = true;
    bool requireObjectives = true;
};

struct EligibilityResult {
    bool eligible = false;
    int approvals = 0;
    double averageScore = 0.0;
    vector<string> reasons;
};

class CommunicationGovernanceEngine {
private:
    map<string, Stakeholder> stakeholders;
    map<int, Communication> communications;
    vector<Review> reviews;
    vector<ReviewComment> comments;
    vector<string> auditLog;

    BranchPolicy policy;
    int nextCommunicationId = 1001;

    void audit(const string& message) {
        auditLog.push_back(message);
    }

    Stakeholder& getStakeholder(const string& id) {
        auto it = stakeholders.find(id);

        if (it == stakeholders.end()) {
            throw invalid_argument("Stakeholder not found: " + id);
        }

        return it->second;
    }

    Communication& getCommunication(int id) {
        auto it = communications.find(id);

        if (it == communications.end()) {
            throw invalid_argument("Communication not found.");
        }

        return it->second;
    }

    void transition(
        Communication& communication,
        Status next,
        const string& actor
    ) {
        map<Status, set<Status>> allowed = {
            {Status::Draft, {Status::Submitted}},
            {Status::Submitted, {Status::UnderReview, Status::Rejected}},
            {Status::UnderReview, {
                Status::RevisionRequired,
                Status::Rejected,
                Status::Approved
            }},
            {Status::RevisionRequired, {Status::Submitted}},
            {Status::Approved, {Status::Published}},
            {Status::Published, {Status::Archived}},
            {Status::Rejected, {Status::Archived}},
            {Status::Archived, {}}
        };

        if (!allowed[communication.status].count(next)) {
            throw logic_error("Invalid communication state transition.");
        }

        Status previous = communication.status;
        communication.status = next;

        audit(
            actor + ": " + toString(previous) +
            " -> " + toString(next)
        );
    }

    bool hasReviewerAlreadyReviewed(
        int communicationId,
        const string& reviewerId
    ) const {
        return any_of(
            reviews.begin(),
            reviews.end(),
            [&](const Review& review) {
                return review.communicationId == communicationId &&
                       review.reviewerId == reviewerId;
            }
        );
    }

public:
    explicit CommunicationGovernanceEngine(
        BranchPolicy configuration = {}
    ) : policy(configuration) {
        if (
            policy.requiredApprovals < 1 ||
            policy.minimumScore < 0 ||
            policy.minimumScore > 100
        ) {
            throw invalid_argument("Invalid governance policy.");
        }
    }

    void registerStakeholder(const Stakeholder& stakeholder) {
        if (
            stakeholder.id.empty() ||
            stakeholder.name.empty() ||
            stakeholder.department.empty()
        ) {
            throw invalid_argument("Invalid stakeholder information.");
        }

        if (stakeholders.count(stakeholder.id)) {
            throw invalid_argument("Duplicate stakeholder.");
        }

        stakeholders.emplace(stakeholder.id, stakeholder);
        audit("Stakeholder registered: " + stakeholder.id);
    }

    int createCommunication(
        const string& title,
        const string& subject,
        const string& content,
        const string& senderId,
        const vector<string>& recipients,
        const vector<string>& objectives,
        CommunicationType type,
        bool acknowledgementRequired = false
    ) {
        if (
            title.empty() ||
            subject.empty() ||
            content.empty() ||
            recipients.empty()
        ) {
            throw invalid_argument("Required communication fields are missing.");
        }

        Stakeholder& sender = getStakeholder(senderId);

        if (!sender.active) {
            throw logic_error("Inactive sender.");
        }

        if (policy.requireObjectives && objectives.empty()) {
            throw invalid_argument("Communication objectives are required.");
        }

        set<string> uniqueRecipients;

        for (const string& recipientId : recipients) {
            Stakeholder& recipient = getStakeholder(recipientId);

            if (!recipient.active) {
                throw logic_error("Inactive recipient.");
            }

            if (!uniqueRecipients.insert(recipientId).second) {
                throw invalid_argument("Duplicate recipient.");
            }
        }

        Communication communication;
        communication.id = nextCommunicationId++;
        communication.title = title;
        communication.subject = subject;
        communication.content = content;
        communication.senderId = senderId;
        communication.recipients = recipients;
        communication.objectives = objectives;
        communication.type = type;
        communication.acknowledgementRequired =
            acknowledgementRequired;

        int id = communication.id;
        communications.emplace(id, communication);

        audit("Communication created: " + to_string(id));

        return id;
    }

    void submit(int id, const string& actorId) {
        Communication& communication = getCommunication(id);

        if (communication.senderId != actorId) {
            throw logic_error("Only the sender can submit.");
        }

        transition(communication, Status::Submitted, actorId);
    }

    void beginReview(int id, const string& reviewerId) {
        Communication& communication = getCommunication(id);
        Stakeholder& reviewer = getStakeholder(reviewerId);

        if (!reviewer.active) {
            throw logic_error("Reviewer is inactive.");
        }

        if (reviewerId == communication.senderId) {
            throw logic_error("Self-review is prohibited.");
        }

        if (
            communication.status != Status::Submitted &&
            communication.status != Status::UnderReview
        ) {
            throw logic_error("Communication is not reviewable.");
        }

        if (communication.status == Status::Submitted) {
            transition(communication, Status::UnderReview, reviewerId);
        }
    }

    void addComment(
        int id,
        const string& reviewerId,
        const string& criterion,
        const string& message,
        Severity severity
    ) {
        Communication& communication = getCommunication(id);
        getStakeholder(reviewerId);

        if (reviewerId == communication.senderId) {
            throw logic_error("Sender cannot review own communication.");
        }

        if (communication.status != Status::UnderReview) {
            throw logic_error("Review is not active.");
        }

        if (criterion.empty() || message.empty()) {
            throw invalid_argument("Comment fields are required.");
        }

        comments.push_back({
            id,
            reviewerId,
            criterion,
            message,
            severity,
            false
        });

        audit("Review comment added to communication " + to_string(id));
    }

    void resolveComment(
        int id,
        size_t commentIndex,
        const string& actorId
    ) {
        Communication& communication = getCommunication(id);

        if (communication.senderId != actorId) {
            throw logic_error("Only the sender can resolve comments.");
        }

        vector<size_t> matching;

        for (size_t i = 0; i < comments.size(); ++i) {
            if (comments[i].communicationId == id) {
                matching.push_back(i);
            }
        }

        if (commentIndex >= matching.size()) {
            throw out_of_range("Comment index not found.");
        }

        comments[matching[commentIndex]].resolved = true;
        audit("Review comment resolved.");
    }

    void recordReview(
        int id,
        const string& reviewerId,
        const map<string, double>& scores,
        Decision decision,
        const string& feedback
    ) {
        Communication& communication = getCommunication(id);
        Stakeholder& reviewer = getStakeholder(reviewerId);

        if (!reviewer.active) {
            throw logic_error("Reviewer is inactive.");
        }

        if (reviewerId == communication.senderId) {
            throw logic_error("Self-review is prohibited.");
        }

        if (communication.status != Status::UnderReview) {
            throw logic_error("Review is not active.");
        }

        if (hasReviewerAlreadyReviewed(id, reviewerId)) {
            throw logic_error("Duplicate reviewer decision.");
        }

        const vector<string> required = {
            "clarity",
            "accuracy",
            "completeness",
            "audience_alignment",
            "timeliness",
            "actionability",
            "professionalism"
        };

        for (const string& criterion : required) {
            if (!scores.count(criterion)) {
                throw invalid_argument(
                    "Missing review criterion: " + criterion
                );
            }
        }

        if (scores.empty()) {
            throw invalid_argument("Review scores cannot be empty.");
        }

        double total = 0.0;

        for (const auto& [criterion, score] : scores) {
            if (
                criterion.empty() ||
                !isfinite(score) ||
                score < 0 ||
                score > 100
            ) {
                throw invalid_argument("Invalid review score.");
            }

            total += score;
        }

        double average = total / scores.size();

        if (
            decision == Decision::Approve &&
            average < policy.minimumScore
        ) {
            throw logic_error("Approval threshold not satisfied.");
        }

        reviews.push_back({
            id,
            reviewerId,
            decision,
            average,
            communication.version,
            feedback
        });

        audit(
            "Review recorded: " + reviewerId +
            " - " + toString(decision)
        );

        if (decision == Decision::Reject) {
            transition(communication, Status::Rejected, reviewerId);
        } else if (decision == Decision::Revise) {
            transition(
                communication,
                Status::RevisionRequired,
                reviewerId
            );
        }
    }

    EligibilityResult evaluate(int id) {
        Communication& communication = getCommunication(id);

        vector<Review> currentReviews;

        for (const Review& review : reviews) {
            if (
                review.communicationId == id &&
                review.version == communication.version
            ) {
                currentReviews.push_back(review);
            }
        }

        EligibilityResult result;

        int rejected = 0;
        int revisionRequests = 0;
        double totalScore = 0.0;

        for (const Review& review : currentReviews) {
            totalScore += review.score;

            const Stakeholder& reviewer =
                stakeholders.at(review.reviewerId);

            if (
                review.decision == Decision::Approve &&
                reviewer.active &&
                review.score >= policy.minimumScore
            ) {
                ++result.approvals;
            }

            if (review.decision == Decision::Reject) {
                ++rejected;
            }

            if (review.decision == Decision::Revise) {
                ++revisionRequests;
            }
        }

        if (!currentReviews.empty()) {
            result.averageScore =
                totalScore / currentReviews.size();
        }

        if (result.approvals < policy.requiredApprovals) {
            result.reasons.push_back(
                "Insufficient eligible approvals."
            );
        }

        if (rejected > 0) {
            result.reasons.push_back("Communication rejected.");
        }

        if (revisionRequests > 0) {
            result.reasons.push_back("Revision requested.");
        }

        if (policy.blockCriticalComments) {
            int unresolvedCritical = count_if(
                comments.begin(),
                comments.end(),
                [&](const ReviewComment& comment) {
                    return comment.communicationId == id &&
                           comment.severity == Severity::Critical &&
                           !comment.resolved;
                }
            );

            if (unresolvedCritical > 0) {
                result.reasons.push_back(
                    "Unresolved critical review comments."
                );
            }
        }

        result.eligible = result.reasons.empty();

        return result;
    }

    void approvePublication(int id, const string& actorId) {
        Communication& communication = getCommunication(id);

        if (communication.senderId != actorId) {
            throw logic_error("Only the sender can authorize publication.");
        }

        if (communication.status != Status::UnderReview) {
            throw logic_error("Communication is not under review.");
        }

        EligibilityResult result = evaluate(id);

        if (!result.eligible) {
            throw logic_error(
                "Publication blocked by governance policy."
            );
        }

        transition(communication, Status::Approved, actorId);
    }

    void publish(int id, const string& actorId) {
        Communication& communication = getCommunication(id);

        if (communication.senderId != actorId) {
            throw logic_error("Only the sender can publish.");
        }

        if (communication.status != Status::Approved) {
            throw logic_error("Communication must be approved.");
        }

        transition(communication, Status::Published, actorId);
    }

    void updateContent(
        int id,
        const string& actorId,
        const string& newContent
    ) {
        Communication& communication = getCommunication(id);

        if (communication.senderId != actorId) {
            throw logic_error("Only the sender can edit.");
        }

        if (
            communication.status == Status::Published ||
            communication.status == Status::Archived
        ) {
            throw logic_error("Published content cannot be modified.");
        }

        if (newContent.empty()) {
            throw invalid_argument("New content cannot be empty.");
        }

        communication.content = newContent;
        ++communication.version;

        reviews.erase(
            remove_if(
                reviews.begin(),
                reviews.end(),
                [&](const Review& review) {
                    return review.communicationId == id;
                }
            ),
            reviews.end()
        );

        transition(
            communication,
            Status::RevisionRequired,
            actorId
        );
    }

    void recordDelivery(
        int id,
        int delivered,
        int read,
        int acknowledged
    ) {
        Communication& communication = getCommunication(id);

        if (communication.status != Status::Published) {
            throw logic_error("Communication is not published.");
        }

        int total = static_cast<int>(
            communication.recipients.size()
        );

        if (
            delivered < 0 ||
            acknowledged < 0 ||
            acknowledged > read ||
            read > delivered ||
            delivered > total
        ) {
            throw invalid_argument("Invalid delivery metrics.");
        }

        communication.delivered = delivered;
        communication.read = read;
        communication.acknowledged = acknowledged;

        audit("Delivery metrics recorded.");
    }

    void printCommunication(int id) {
        const Communication& communication = communications.at(id);

        cout << "\nCOMMUNICATION " << communication.id << "\n";
        cout << "Title: " << communication.title << "\n";
        cout << "Subject: " << communication.subject << "\n";
        cout << "Status: " << toString(communication.status) << "\n";
        cout << "Version: " << communication.version << "\n";
        cout << "Recipients: " << communication.recipients.size() << "\n";
    }

    void printEligibility(int id) {
        EligibilityResult result = evaluate(id);

        cout << "\nMERGE-STYLE PUBLICATION ELIGIBILITY\n";
        cout << "Eligible: "
             << (result.eligible ? "YES" : "NO") << "\n";

        cout << "Valid approvals: " << result.approvals << "\n";
        cout << "Average score: "
             << fixed << setprecision(2)
             << result.averageScore << "\n";

        for (const string& reason : result.reasons) {
            cout << "Blocked: " << reason << "\n";
        }
    }

    void printPerformance(int id) {
        const Communication& communication = communications.at(id);

        double total = communication.recipients.size();

        double deliveryRate =
            total ? communication.delivered / total * 100.0 : 0.0;

        double readRate =
            total ? communication.read / total * 100.0 : 0.0;

        double acknowledgementRate =
            total ? communication.acknowledged / total * 100.0 : 0.0;

        cout << "\nCOMMUNICATION PERFORMANCE\n";
        cout << "Delivery rate: " << deliveryRate << "%\n";
        cout << "Read rate: " << readRate << "%\n";
        cout << "Acknowledgement rate: "
             << acknowledgementRate << "%\n";

        cout << "Delivery target: "
             << (deliveryRate >= policy.minimumDeliveryRate
                 ? "MET" : "NOT MET") << "\n";

        cout << "Acknowledgement target: "
             << (
                 !communication.acknowledgementRequired ||
                 acknowledgementRate >= policy.minimumAcknowledgementRate
                 ? "MET" : "NOT MET"
             ) << "\n";
    }

    void printAuditLog() const {
        cout << "\nAUDIT LOG\n";

        for (const string& event : auditLog) {
            cout << "- " << event << "\n";
        }
    }
};

int main() {
    try {
        BranchPolicy policy;
        policy.requiredApprovals = 2;
        policy.minimumScore = 70.0;

        CommunicationGovernanceEngine engine(policy);

        engine.registerStakeholder({
            "EMP001", "Project Manager",
            "Manager", "Operations", true
        });

        engine.registerStakeholder({
            "EMP002", "Quality Officer",
            "Reviewer", "Quality", true
        });

        engine.registerStakeholder({
            "EMP003", "Technical Lead",
            "Reviewer", "Technology", true
        });

        engine.registerStakeholder({
            "EMP004", "Department Head",
            "Recipient", "Management", true
        });

        engine.registerStakeholder({
            "EMP005", "Field Coordinator",
            "Recipient", "Operations", true
        });

        int id = engine.createCommunication(
            "Monthly Operational Review",
            "Performance and Corrective Actions",
            "The report communicates operational results, "
            "pending activities, identified risks, and actions.",
            "EMP001",
            {"EMP004", "EMP005"},
            {
                "Report operational performance",
                "Identify risks",
                "Assign corrective actions"
            },
            CommunicationType::Report,
            true
        );

        engine.submit(id, "EMP001");

        const map<string, double> scores = {
            {"clarity", 92},
            {"accuracy", 95},
            {"completeness", 90},
            {"audience_alignment", 88},
            {"timeliness", 90},
            {"actionability", 93},
            {"professionalism", 96}
        };

        engine.beginReview(id, "EMP002");

        engine.addComment(
            id,
            "EMP002",
            "accuracy",
            "Verify reported figures against original records.",
            Severity::Medium
        );

        engine.recordReview(
            id,
            "EMP002",
            scores,
            Decision::Approve,
            "The report meets the review criteria."
        );

        engine.beginReview(id, "EMP003");

        engine.recordReview(
            id,
            "EMP003",
            scores,
            Decision::Approve,
            "The technical information is accurate."
        );

        engine.printCommunication(id);
        engine.printEligibility(id);

        engine.approvePublication(id, "EMP001");
        engine.publish(id, "EMP001");

        engine.recordDelivery(id, 2, 2, 2);

        engine.printCommunication(id);
        engine.printPerformance(id);
        engine.printAuditLog();

    } catch (const exception& error) {
        cerr << "SYSTEM ERROR: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
