#include <algorithm>
#include <chrono>
#include <cmath>
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

enum class Category {
    UnclearMessage,
    InformationOverload,
    PoorListening,
    LanguageBarrier,
    CulturalDifference,
    WrongChannel,
    DelayedResponse,
    MissingFeedback,
    IncorrectAssumption,
    TechnicalFailure,
    InterpersonalConflict,
    RoleAmbiguity
};

enum class Severity {
    Low,
    Medium,
    High,
    Critical
};

enum class Channel {
    Email,
    Meeting,
    Chat,
    Phone,
    Document,
    VideoConference,
    FaceToFace
};

enum class Status {
    Open,
    Investigating,
    ActionRequired,
    Resolved,
    Closed
};

enum class ReviewDecision {
    NotReviewed,
    Accepted,
    Rejected
};

string toString(Category category) {
    static const map<Category, string> names = {
        {Category::UnclearMessage, "Unclear message"},
        {Category::InformationOverload, "Information overload"},
        {Category::PoorListening, "Poor listening"},
        {Category::LanguageBarrier, "Language barrier"},
        {Category::CulturalDifference, "Cultural difference"},
        {Category::WrongChannel, "Wrong communication channel"},
        {Category::DelayedResponse, "Delayed response"},
        {Category::MissingFeedback, "Missing feedback"},
        {Category::IncorrectAssumption, "Incorrect assumption"},
        {Category::TechnicalFailure, "Technical failure"},
        {Category::InterpersonalConflict, "Interpersonal conflict"},
        {Category::RoleAmbiguity, "Role ambiguity"}
    };

    return names.at(category);
}

string toString(Severity severity) {
    switch (severity) {
        case Severity::Low: return "LOW";
        case Severity::Medium: return "MEDIUM";
        case Severity::High: return "HIGH";
        case Severity::Critical: return "CRITICAL";
    }

    throw invalid_argument("Unknown severity.");
}

string toString(Status status) {
    switch (status) {
        case Status::Open: return "OPEN";
        case Status::Investigating: return "INVESTIGATING";
        case Status::ActionRequired: return "ACTION REQUIRED";
        case Status::Resolved: return "RESOLVED";
        case Status::Closed: return "CLOSED";
    }

    throw invalid_argument("Unknown status.");
}

string toString(Channel channel) {
    switch (channel) {
        case Channel::Email: return "Email";
        case Channel::Meeting: return "Meeting";
        case Channel::Chat: return "Chat";
        case Channel::Phone: return "Phone";
        case Channel::Document: return "Document";
        case Channel::VideoConference: return "Video conference";
        case Channel::FaceToFace: return "Face-to-face";
    }

    throw invalid_argument("Unknown channel.");
}

struct StatusCheck {
    string name;
    bool passed;
    string details;
};

struct CommunicationPolicy {
    map<Severity, int> responseHours = {
        {Severity::Low, 72},
        {Severity::Medium, 48},
        {Severity::High, 12},
        {Severity::Critical, 2}
    };

    int requiredApprovals = 1;
    bool requireFeedback = true;
    bool requireCorrectiveAction = true;
};

struct CommunicationIncident {
    int id;
    string title;
    Category category;
    Severity severity;
    Channel channel;

    string department;
    string reporter;
    string assignee;

    string description;
    string correctiveAction;
    string resolution;

    Status status = Status::Open;
    ReviewDecision feedback = ReviewDecision::NotReviewed;

    chrono::system_clock::time_point createdAt =
        chrono::system_clock::now();

    optional<chrono::system_clock::time_point> resolvedAt;

    vector<string> eventLog;
    vector<StatusCheck> checks;

    void record(const string& event) {
        eventLog.push_back(event);
    }
};

class GovernanceEngine {
private:
    map<int, CommunicationIncident> incidents;
    int nextId = 1;
    CommunicationPolicy policy;

    map<Status, set<Status>> allowedTransitions = {
        {
            Status::Open,
            {Status::Investigating, Status::Closed}
        },
        {
            Status::Investigating,
            {
                Status::ActionRequired,
                Status::Resolved,
                Status::Closed
            }
        },
        {
            Status::ActionRequired,
            {Status::Investigating, Status::Resolved}
        },
        {
            Status::Resolved,
            {Status::Closed, Status::Investigating}
        },
        {
            Status::Closed,
            {}
        }
    };

    static string trim(const string& value) {
        const auto first = value.find_first_not_of(" \t\n\r");

        if (first == string::npos) {
            return "";
        }

        const auto last = value.find_last_not_of(" \t\n\r");

        return value.substr(first, last - first + 1);
    }

    static string validate(
        const string& value,
        const string& field,
        size_t maximum
    ) {
        string result = trim(value);

        if (result.empty() || result.size() > maximum) {
            throw invalid_argument(field + " has invalid length.");
        }

        if (result.find('\0') != string::npos) {
            throw invalid_argument(field + " contains invalid data.");
        }

        return result;
    }

public:
    CommunicationIncident& get(int id) {
        auto iterator = incidents.find(id);

        if (iterator == incidents.end()) {
            throw out_of_range("Communication incident not found.");
        }

        return iterator->second;
    }

    const CommunicationIncident& get(int id) const {
        auto iterator = incidents.find(id);

        if (iterator == incidents.end()) {
            throw out_of_range("Communication incident not found.");
        }

        return iterator->second;
    }

    int report(
        string title,
        Category category,
        Severity severity,
        Channel channel,
        string department,
        string reporter,
        string description
    ) {
        CommunicationIncident incident;

        incident.id = nextId++;
        incident.title = validate(title, "Title", 120);
        incident.category = category;
        incident.severity = severity;
        incident.channel = channel;

        incident.department = validate(
            department, "Department", 100
        );

        incident.reporter = validate(
            reporter, "Reporter", 100
        );

        incident.description = validate(
            description, "Description", 1000
        );

        incident.record("Incident registered.");

        int id = incident.id;

        incidents.emplace(id, move(incident));

        return id;
    }

    void assign(int id, const string& employee) {
        auto& incident = get(id);

        if (incident.status == Status::Closed) {
            throw logic_error("Cannot assign a closed incident.");
        }

        incident.assignee = validate(
            employee, "Assignee", 100
        );

        incident.record("Assigned to " + incident.assignee);
    }

    void transition(int id, Status nextStatus) {
        auto& incident = get(id);

        if (!allowedTransitions.at(incident.status).count(nextStatus)) {
            throw logic_error("Invalid communication state transition.");
        }

        if (
            nextStatus == Status::Resolved &&
            (
                incident.correctiveAction.empty() ||
                incident.resolution.empty()
            )
        ) {
            throw logic_error(
                "Corrective action and resolution are mandatory."
            );
        }

        incident.status = nextStatus;

        if (nextStatus == Status::Resolved) {
            incident.resolvedAt = chrono::system_clock::now();
        }

        incident.record("Status changed to " + toString(nextStatus));
    }

    string recommend(Category category) const {
        static const map<Category, string> actions = {
            {
                Category::UnclearMessage,
                "Rewrite instructions using clear language and explicit deadlines."
            },
            {
                Category::InformationOverload,
                "Prioritize information and divide content into sections."
            },
            {
                Category::PoorListening,
                "Use active listening and paraphrasing."
            },
            {
                Category::LanguageBarrier,
                "Use plain language and verified translation."
            },
            {
                Category::CulturalDifference,
                "Establish inclusive communication practices."
            },
            {
                Category::WrongChannel,
                "Select a channel suitable for urgency and confidentiality."
            },
            {
                Category::DelayedResponse,
                "Introduce response deadlines and escalation procedures."
            },
            {
                Category::MissingFeedback,
                "Establish acknowledgement and feedback cycles."
            },
            {
                Category::IncorrectAssumption,
                "Verify facts and confirm understanding."
            },
            {
                Category::TechnicalFailure,
                "Verify communication infrastructure and backup channels."
            },
            {
                Category::InterpersonalConflict,
                "Use structured discussion and impartial mediation."
            },
            {
                Category::RoleAmbiguity,
                "Define ownership, responsibilities and reporting lines."
            }
        };

        return actions.at(category);
    }

    void prescribeAction(int id, string action = "") {
        auto& incident = get(id);

        if (incident.status == Status::Closed) {
            throw logic_error("Incident is already closed.");
        }

        if (action.empty()) {
            action = recommend(incident.category);
        }

        incident.correctiveAction = validate(
            action, "Corrective action", 1000
        );

        incident.record("Corrective action prescribed.");

        if (
            incident.status == Status::Open ||
            incident.status == Status::Investigating
        ) {
            transition(id, Status::ActionRequired);
        }
    }

    void resolve(int id, string resolution) {
        auto& incident = get(id);

        if (
            incident.status != Status::Investigating &&
            incident.status != Status::ActionRequired
        ) {
            throw logic_error(
                "Incident must be investigated before resolution."
            );
        }

        incident.resolution = validate(
            resolution, "Resolution", 1000
        );

        transition(id, Status::Resolved);
    }

    void recordFeedback(int id, ReviewDecision decision) {
        auto& incident = get(id);

        if (incident.status != Status::Resolved) {
            throw logic_error(
                "Feedback is accepted only after resolution."
            );
        }

        if (decision == ReviewDecision::NotReviewed) {
            throw invalid_argument("Feedback decision is required.");
        }

        incident.feedback = decision;

        incident.record(
            decision == ReviewDecision::Accepted
                ? "Resolution accepted."
                : "Resolution rejected."
        );

        if (decision == ReviewDecision::Rejected) {
            transition(id, Status::Investigating);
        }
    }

    void close(int id) {
        auto& incident = get(id);

        if (
            policy.requireFeedback &&
            incident.feedback != ReviewDecision::Accepted
        ) {
            throw logic_error(
                "Accepted feedback is required before closure."
            );
        }

        if (
            policy.requireCorrectiveAction &&
            incident.correctiveAction.empty()
        ) {
            throw logic_error(
                "Corrective action is required before closure."
            );
        }

        transition(id, Status::Closed);
    }

    void addStatusCheck(
        int id,
        string name,
        bool passed,
        string details
    ) {
        auto& incident = get(id);

        name = validate(name, "Check name", 100);
        details = validate(details, "Check details", 500);

        incident.checks.push_back({
            name,
            passed,
            details
        });

        incident.record(
            "Status check: " + name +
            (passed ? " passed." : " failed.")
        );
    }

    struct Eligibility {
        bool eligible;
        vector<string> failures;
    };

    Eligibility evaluate(int id) const {
        const auto& incident = get(id);

        Eligibility result{true, {}};

        auto reject = [&](const string& reason) {
            result.eligible = false;
            result.failures.push_back(reason);
        };

        if (incident.status != Status::Resolved) {
            reject("Incident must be resolved.");
        }

        if (incident.correctiveAction.empty()) {
            reject("Corrective action is missing.");
        }

        if (incident.resolution.empty()) {
            reject("Resolution documentation is missing.");
        }

        if (
            policy.requireFeedback &&
            incident.feedback != ReviewDecision::Accepted
        ) {
            reject("Resolution feedback is not accepted.");
        }

        for (const auto& check : incident.checks) {
            if (!check.passed) {
                reject("Failed status check: " + check.name);
            }
        }

        return result;
    }

    vector<CommunicationIncident> search(
        optional<Category> category = nullopt,
        optional<Status> status = nullopt
    ) const {
        vector<CommunicationIncident> results;

        for (const auto& [id, incident] : incidents) {
            if (category && incident.category != *category) {
                continue;
            }

            if (status && incident.status != *status) {
                continue;
            }

            results.push_back(incident);
        }

        return results;
    }

    void printReport() const {
        map<Category, int> categoryCounts;
        map<Severity, int> severityCounts;
        map<Status, int> statusCounts;

        int resolved = 0;
        double resolutionHours = 0.0;
        int durationCount = 0;

        cout << "\nCOMMUNICATION INCIDENT REGISTER\n";

        for (const auto& [id, incident] : incidents) {
            cout << "\nID: " << id
                 << "\nTitle: " << incident.title
                 << "\nCategory: " << toString(incident.category)
                 << "\nSeverity: " << toString(incident.severity)
                 << "\nChannel: " << toString(incident.channel)
                 << "\nDepartment: " << incident.department
                 << "\nStatus: " << toString(incident.status)
                 << "\nAssignee: "
                 << (
                     incident.assignee.empty()
                         ? "Unassigned"
                         : incident.assignee
                 )
                 << "\n";

            categoryCounts[incident.category]++;
            severityCounts[incident.severity]++;
            statusCounts[incident.status]++;

            if (incident.resolvedAt) {
                ++resolved;

                auto duration = chrono::duration<double>(
                    *incident.resolvedAt - incident.createdAt
                );

                resolutionHours += duration.count() / 3600.0;
                ++durationCount;
            }
        }

        double rate = incidents.empty()
            ? 0.0
            : 100.0 * resolved / incidents.size();

        cout << "\nANALYTICS\n"
             << "Total incidents: " << incidents.size() << "\n"
             << "Resolved rate: " << fixed << setprecision(2)
             << rate << "%\n";

        if (durationCount > 0) {
            cout << "Average resolution hours: "
                 << resolutionHours / durationCount << "\n";
        }

        cout << "\nCATEGORY DISTRIBUTION\n";

        for (const auto& [category, count] : categoryCounts) {
            cout << toString(category) << ": " << count << "\n";
        }

        cout << "\nSTATUS DISTRIBUTION\n";

        for (const auto& [status, count] : statusCounts) {
            cout << toString(status) << ": " << count << "\n";
        }
    }
};

int main() {
    try {
        GovernanceEngine engine;

        int first = engine.report(
            "Unclear project instructions",
            Category::UnclearMessage,
            Severity::High,
            Channel::Email,
            "Engineering",
            "Project Manager",
            "Different teams interpreted delivery requirements differently."
        );

        engine.assign(first, "Engineering Coordinator");

        engine.transition(first, Status::Investigating);

        engine.prescribeAction(first);

        engine.resolve(
            first,
            "A revised project document clarified responsibilities and deadlines."
        );

        engine.recordFeedback(
            first,
            ReviewDecision::Accepted
        );

        auto eligibility = engine.evaluate(first);

        cout << "\nRESOLUTION ELIGIBILITY: "
             << (eligibility.eligible ? "APPROVED" : "REJECTED")
             << "\n";

        for (const auto& failure : eligibility.failures) {
            cout << "- " << failure << "\n";
        }

        engine.close(first);

        int second = engine.report(
            "Delayed customer response",
            Category::DelayedResponse,
            Severity::Medium,
            Channel::Email,
            "Customer Support",
            "Support Manager",
            "A customer request remained unanswered beyond the expected time."
        );

        engine.assign(second, "Support Team Lead");
        engine.transition(second, Status::Investigating);
        engine.prescribeAction(second);

        engine.addStatusCheck(
            second,
            "Escalation procedure configured",
            true,
            "An escalation owner has been assigned."
        );

        int third = engine.report(
            "Information overload",
            Category::InformationOverload,
            Severity::Low,
            Channel::Meeting,
            "Operations",
            "Operations Supervisor",
            "Meeting participants received excessive unstructured information."
        );

        cout << "\nOPEN COMMUNICATION ISSUES: "
             << engine.search(
                    nullopt,
                    Status::Open
                ).size()
             << "\n";

        engine.printReport();

        // Verify invalid transitions are rejected.
        bool invalidTransitionRejected = false;

        try {
            engine.transition(first, Status::Investigating);
        } catch (const logic_error&) {
            invalidTransitionRejected = true;
        }

        if (!invalidTransitionRejected) {
            throw runtime_error("State validation test failed.");
        }

        cout << "\nValidation test passed.\n";

    } catch (const exception& error) {
        cerr << "Application error: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
