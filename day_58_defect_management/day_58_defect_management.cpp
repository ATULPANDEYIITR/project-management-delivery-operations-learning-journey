#include <algorithm>
#include <chrono>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

enum class Severity { Blocker, Critical, Major, Minor, Trivial };
enum class Priority { P0, P1, P2, P3 };
enum class DefectStatus {
    New,
    Triaged,
    Assigned,
    InProgress,
    Resolved,
    Verified,
    Reopened,
    Closed,
    Rejected
};

std::string to_string(Severity value) {
    switch (value) {
        case Severity::Blocker: return "BLOCKER";
        case Severity::Critical: return "CRITICAL";
        case Severity::Major: return "MAJOR";
        case Severity::Minor: return "MINOR";
        case Severity::Trivial: return "TRIVIAL";
    }
    return "UNKNOWN";
}

std::string to_string(Priority value) {
    switch (value) {
        case Priority::P0: return "P0";
        case Priority::P1: return "P1";
        case Priority::P2: return "P2";
        case Priority::P3: return "P3";
    }
    return "UNKNOWN";
}

std::string to_string(DefectStatus value) {
    switch (value) {
        case DefectStatus::New: return "NEW";
        case DefectStatus::Triaged: return "TRIAGED";
        case DefectStatus::Assigned: return "ASSIGNED";
        case DefectStatus::InProgress: return "IN_PROGRESS";
        case DefectStatus::Resolved: return "RESOLVED";
        case DefectStatus::Verified: return "VERIFIED";
        case DefectStatus::Reopened: return "REOPENED";
        case DefectStatus::Closed: return "CLOSED";
        case DefectStatus::Rejected: return "REJECTED";
    }
    return "UNKNOWN";
}

int severity_weight(Severity value) {
    switch (value) {
        case Severity::Blocker: return 5;
        case Severity::Critical: return 4;
        case Severity::Major: return 3;
        case Severity::Minor: return 2;
        case Severity::Trivial: return 1;
    }
    return 0;
}

int priority_weight(Priority value) {
    switch (value) {
        case Priority::P0: return 4;
        case Priority::P1: return 3;
        case Priority::P2: return 2;
        case Priority::P3: return 1;
    }
    return 0;
}

struct ReviewCheck {
    std::string name;
    bool passed{};
};

struct Defect {
    int id{};
    std::string title;
    std::string component;
    Severity severity{};
    Priority priority{};
    DefectStatus status{DefectStatus::New};
    int reporter{};
    std::optional<int> assignee;
    std::string resolution;
    std::vector<std::string> history;

    void audit(const std::string& message) {
        history.push_back(message);
    }
};

class GovernanceEngine {
private:
    std::map<int, Defect> defects_;
    int next_id_ = 7000;

    static bool terminal(DefectStatus status) {
        return status == DefectStatus::Closed ||
               status == DefectStatus::Rejected;
    }

    Defect& get(int id) {
        auto it = defects_.find(id);
        if (it == defects_.end()) {
            throw std::out_of_range("Defect does not exist.");
        }
        return it->second;
    }

public:
    int create(
        std::string title,
        std::string component,
        Severity severity,
        Priority priority,
        int reporter
    ) {
        if (title.empty() || component.empty()) {
            throw std::invalid_argument("Title and component are required.");
        }

        const int id = next_id_++;
        Defect defect{
            id,
            std::move(title),
            std::move(component),
            severity,
            priority,
            DefectStatus::New,
            reporter,
            std::nullopt,
            "",
            {}
        };
        defect.audit("Created by reporter " + std::to_string(reporter));
        defects_.emplace(id, std::move(defect));
        return id;
    }

    void triage(int id, int actor) {
        Defect& defect = get(id);
        if (defect.status != DefectStatus::New) {
            throw std::logic_error("Only NEW defects can be triaged.");
        }
        defect.status = DefectStatus::Triaged;
        defect.audit("Triaged by " + std::to_string(actor));
    }

    void assign(int id, int actor, int assignee) {
        Defect& defect = get(id);
        if (defect.status != DefectStatus::Triaged &&
            defect.status != DefectStatus::Reopened) {
            throw std::logic_error("Defect is not assignable in its current state.");
        }
        defect.assignee = assignee;
        defect.status = DefectStatus::Assigned;
        defect.audit(
            "Assigned by " + std::to_string(actor) +
            " to " + std::to_string(assignee)
        );
    }

    void start(int id, int actor) {
        Defect& defect = get(id);
        if (!defect.assignee || *defect.assignee != actor) {
            throw std::permission_denied("Only the assignee may start work.");
        }
        if (defect.status != DefectStatus::Assigned) {
            throw std::logic_error("Defect must be ASSIGNED.");
        }
        defect.status = DefectStatus::InProgress;
        defect.audit("Work started by " + std::to_string(actor));
    }

    void resolve(int id, int actor, std::string resolution) {
        Defect& defect = get(id);
        if (!defect.assignee || *defect.assignee != actor) {
            throw std::permission_denied("Only the assignee may resolve.");
        }
        if (defect.status != DefectStatus::InProgress) {
            throw std::logic_error("Defect must be IN_PROGRESS.");
        }
        if (resolution.empty()) {
            throw std::invalid_argument("Resolution cannot be empty.");
        }
        defect.resolution = std::move(resolution);
        defect.status = DefectStatus::Resolved;
        defect.audit("Resolved by " + std::to_string(actor));
    }

    void verify(int id, int tester, bool passed) {
        Defect& defect = get(id);
        if (defect.status != DefectStatus::Resolved) {
            throw std::logic_error("Only RESOLVED defects can be verified.");
        }

        defect.status = passed ? DefectStatus::Verified : DefectStatus::Reopened;
        defect.audit(
            std::string("Verification by ") + std::to_string(tester) +
            (passed ? ": PASSED" : ": FAILED; REOPENED")
        );
    }

    void close(int id, int actor) {
        Defect& defect = get(id);
        if (defect.status != DefectStatus::Verified) {
            throw std::logic_error("Only VERIFIED defects can be closed.");
        }
        defect.status = DefectStatus::Closed;
        defect.audit("Closed by " + std::to_string(actor));
    }

    bool merge_eligible(
        int id,
        const std::vector<ReviewCheck>& checks,
        int required_approvals,
        int actual_approvals,
        bool conversations_resolved,
        bool security_owner_approved
    ) const {
        auto it = defects_.find(id);
        if (it == defects_.end()) {
            throw std::out_of_range("Defect does not exist.");
        }

        const Defect& defect = it->second;

        if (terminal(defect.status) && defect.status == DefectStatus::Rejected) {
            return false;
        }

        if (defect.severity == Severity::Blocker ||
            defect.severity == Severity::Critical) {
            if (!security_owner_approved) {
                return false;
            }
        }

        for (const auto& check : checks) {
            if (!check.passed) {
                return false;
            }
        }

        return actual_approvals >= required_approvals &&
               conversations_resolved;
    }

    std::vector<Defect> prioritized_open_defects() const {
        std::vector<Defect> result;
        for (const auto& [id, defect] : defects_) {
            if (!terminal(defect.status)) {
                result.push_back(defect);
            }
        }

        std::sort(result.begin(), result.end(),
            [](const Defect& a, const Defect& b) {
                if (severity_weight(a.severity) != severity_weight(b.severity)) {
                    return severity_weight(a.severity) >
                           severity_weight(b.severity);
                }
                if (priority_weight(a.priority) != priority_weight(b.priority)) {
                    return priority_weight(a.priority) >
                           priority_weight(b.priority);
                }
                return a.id < b.id;
            });

        return result;
    }

    const Defect& get_const(int id) const {
        auto it = defects_.find(id);
        if (it == defects_.end()) {
            throw std::out_of_range("Defect does not exist.");
        }
        return it->second;
    }
};

int main() {
    try {
        GovernanceEngine engine;

        const int security_defect = engine.create(
            "Authentication bypass under stale session",
            "authentication",
            Severity::Critical,
            Priority::P0,
            100
        );

        const int ui_defect = engine.create(
            "Dashboard label overlaps at narrow width",
            "dashboard",
            Severity::Minor,
            Priority::P3,
            101
        );

        engine.triage(security_defect, 200);
        engine.assign(security_defect, 200, 301);
        engine.start(security_defect, 301);
        engine.resolve(
            security_defect,
            301,
            "Invalidated stale sessions and added server-side authorization checks."
        );

        engine.triage(ui_defect, 200);
        engine.assign(ui_defect, 200, 302);
        engine.start(ui_defect, 302);
        engine.resolve(
            ui_defect,
            302,
            "Adjusted responsive layout constraints."
        );
        engine.verify(ui_defect, 401, false);
        engine.assign(ui_defect, 200, 302);
        engine.start(ui_defect, 302);

        const std::vector<ReviewCheck> checks{
            {"unit-tests", true},
            {"integration-tests", true},
            {"security-scan", true}
        };

        const bool eligible = engine.merge_eligible(
            security_defect,
            checks,
            2,
            2,
            true,
            true
        );

        std::cout << "Security defect merge/governance decision: "
                  << (eligible ? "ELIGIBLE" : "BLOCKED") << "\n\n";

        std::cout << "Prioritized open defects:\n";
        for (const auto& defect : engine.prioritized_open_defects()) {
            std::cout
                << defect.id << " | "
                << defect.component << " | "
                << to_string(defect.severity) << " | "
                << to_string(defect.priority) << " | "
                << to_string(defect.status) << "\n";
        }

        // Explicit failure handling: invalid state transition must not mutate state.
        const auto before = engine.get_const(security_defect).status;
        try {
            engine.close(security_defect, 200);
        } catch (const std::exception& ex) {
            std::cout << "\nExpected transition failure: "
                      << ex.what() << "\n";
        }
        const auto after = engine.get_const(security_defect).status;

        if (before != after) {
            throw std::logic_error("State was mutated after rejected operation.");
        }

        // The second defect remains reopened/in progress after failed verification.
        if (engine.get_const(ui_defect).status != DefectStatus::InProgress) {
            throw std::logic_error("Reopen workflow invariant failed.");
        }

        std::cout << "\nAudit history for security defect:\n";
        for (const auto& event : engine.get_const(security_defect).history) {
            std::cout << " - " << event << "\n";
        }

    } catch (const std::exception& ex) {
        std::cerr << "Fatal error: " << ex.what() << '\n';
        return 1;
    }

    return 0;
}
