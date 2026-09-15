/*
 * Project Charter: Understanding Project Authorization
 *
 * C++17 industry-style case study.
 *
 * Scenario:
 * A financial-services organization wants to authorize a project that will
 * reduce customer-support response time. The program models a governance
 * workflow in which a project charter is reviewed, validated, risk-ranked,
 * authorized, versioned, and used as the baseline for change requests.
 *
 * Compile:
 *     g++ -std=c++17 -O2 -Wall -Wextra -pedantic project_charter.cpp -o project_charter
 */

#include <algorithm>
#include <cassert>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;


// -----------------------------------------------------------------------------
// Utility
// -----------------------------------------------------------------------------

void section(const string& title) {
    cout << "\n" << string(78, '=') << "\n";
    cout << title << "\n";
    cout << string(78, '=') << "\n";
}

string trim(const string& value) {
    const auto first = value.find_first_not_of(" \t\n\r");
    if (first == string::npos) {
        return "";
    }

    const auto last = value.find_last_not_of(" \t\n\r");
    return value.substr(first, last - first + 1);
}


// -----------------------------------------------------------------------------
// 1. Core domain types
// -----------------------------------------------------------------------------

enum class AuthorizationStatus {
    Draft,
    UnderReview,
    Authorized,
    Rejected,
    Suspended
};

enum class Decision {
    Approve,
    Reject,
    RequestRevision
};

string toString(AuthorizationStatus status) {
    switch (status) {
        case AuthorizationStatus::Draft:
            return "Draft";
        case AuthorizationStatus::UnderReview:
            return "Under Review";
        case AuthorizationStatus::Authorized:
            return "Authorized";
        case AuthorizationStatus::Rejected:
            return "Rejected";
        case AuthorizationStatus::Suspended:
            return "Suspended";
    }

    return "Unknown";
}

string toString(Decision decision) {
    switch (decision) {
        case Decision::Approve:
            return "Approve";
        case Decision::Reject:
            return "Reject";
        case Decision::RequestRevision:
            return "Request Revision";
    }

    return "Unknown";
}


// -----------------------------------------------------------------------------
// 2. Objectives
// -----------------------------------------------------------------------------

struct Objective {
    string description;
    bool specific = false;
    bool measurable = false;
    bool achievable = false;
    bool relevant = false;
    bool timeBound = false;

    bool isSMART() const {
        return specific &&
               measurable &&
               achievable &&
               relevant &&
               timeBound;
    }

    int smartScore() const {
        return static_cast<int>(specific) +
               static_cast<int>(measurable) +
               static_cast<int>(achievable) +
               static_cast<int>(relevant) +
               static_cast<int>(timeBound);
    }
};


// -----------------------------------------------------------------------------
// 3. Risks
// -----------------------------------------------------------------------------

struct Risk {
    string id;
    string description;
    double probability;
    double impact;
    string response;

    double exposure() const {
        return probability * impact;
    }

    string severity() const {
        const double value = exposure();

        if (value >= 16.0) {
            return "Critical";
        }

        if (value >= 9.0) {
            return "High";
        }

        if (value >= 4.0) {
            return "Medium";
        }

        return "Low";
    }
};


// -----------------------------------------------------------------------------
// 4. Stakeholders
// -----------------------------------------------------------------------------

struct Stakeholder {
    string name;
    string role;
    int influence;
    int interest;

    string engagementStrategy() const {
        if (influence >= 4 && interest >= 4) {
            return "Manage closely";
        }

        if (influence >= 4) {
            return "Keep satisfied";
        }

        if (interest >= 4) {
            return "Keep informed";
        }

        return "Monitor";
    }
};


// -----------------------------------------------------------------------------
// 5. Milestones
// -----------------------------------------------------------------------------

struct Milestone {
    string name;
    string targetDate;
};


// -----------------------------------------------------------------------------
// 6. Authorization decision
// -----------------------------------------------------------------------------

struct AuthorizationDecision {
    Decision decision;
    string decisionMaker;
    string rationale;
};


// -----------------------------------------------------------------------------
// 7. Change request
// -----------------------------------------------------------------------------

struct ChangeRequest {
    string id;
    string description;
    string requestedBy;
    string scopeImpact;
    double budgetImpact;
    int scheduleImpactDays;

    bool requiresGovernanceReview() const {
        return budgetImpact != 0.0 ||
               scheduleImpactDays != 0 ||
               scopeImpact != "None";
    }
};


// -----------------------------------------------------------------------------
// 8. Project Charter
// -----------------------------------------------------------------------------

class ProjectCharter {
private:
    string projectId_;
    string title_;
    string sponsor_;
    string projectManager_;
    string purpose_;
    string businessCase_;

    vector<string> strategicAlignment_;
    vector<Objective> objectives_;
    vector<string> inScope_;
    vector<string> outOfScope_;
    vector<string> deliverables_;
    vector<Milestone> milestones_;
    vector<string> assumptions_;
    vector<string> constraints_;
    vector<Risk> risks_;
    vector<Stakeholder> stakeholders_;
    vector<string> acceptanceCriteria_;

    double budgetCeiling_ = 0.0;

    AuthorizationStatus status_ = AuthorizationStatus::Draft;
    int version_ = 1;

public:
    ProjectCharter(
        string projectId,
        string title,
        string sponsor,
        string projectManager,
        string purpose,
        string businessCase,
        vector<string> strategicAlignment,
        vector<Objective> objectives,
        vector<string> inScope,
        vector<string> outOfScope,
        vector<string> deliverables,
        vector<Milestone> milestones,
        vector<string> assumptions,
        vector<string> constraints,
        vector<Risk> risks,
        vector<Stakeholder> stakeholders,
        vector<string> acceptanceCriteria,
        double budgetCeiling
    )
        : projectId_(move(projectId)),
          title_(move(title)),
          sponsor_(move(sponsor)),
          projectManager_(move(projectManager)),
          purpose_(move(purpose)),
          businessCase_(move(businessCase)),
          strategicAlignment_(move(strategicAlignment)),
          objectives_(move(objectives)),
          inScope_(move(inScope)),
          outOfScope_(move(outOfScope)),
          deliverables_(move(deliverables)),
          milestones_(move(milestones)),
          assumptions_(move(assumptions)),
          constraints_(move(constraints)),
          risks_(move(risks)),
          stakeholders_(move(stakeholders)),
          acceptanceCriteria_(move(acceptanceCriteria)),
          budgetCeiling_(budgetCeiling) {}

    vector<string> validate() const {
        vector<string> errors;

        if (trim(projectId_).empty()) {
            errors.push_back("Project ID is missing.");
        }

        if (trim(title_).empty()) {
            errors.push_back("Project title is missing.");
        }

        if (trim(sponsor_).empty()) {
            errors.push_back("Sponsor is missing.");
        }

        if (trim(projectManager_).empty()) {
            errors.push_back("Project manager is missing.");
        }

        if (trim(purpose_).empty()) {
            errors.push_back("Project purpose is missing.");
        }

        if (trim(businessCase_).empty()) {
            errors.push_back("Business case is missing.");
        }

        if (objectives_.empty()) {
            errors.push_back("At least one objective is required.");
        } else {
            const bool allSmart = all_of(
                objectives_.begin(),
                objectives_.end(),
                [](const Objective& objective) {
                    return objective.isSMART();
                }
            );

            if (!allSmart) {
                errors.push_back(
                    "Every authorization-level objective should be SMART."
                );
            }
        }

        if (inScope_.empty()) {
            errors.push_back("In-scope definition is missing.");
        }

        if (outOfScope_.empty()) {
            errors.push_back("Out-of-scope definition is missing.");
        }

        if (deliverables_.empty()) {
            errors.push_back("Deliverables are missing.");
        }

        if (milestones_.empty()) {
            errors.push_back("Milestones are missing.");
        }

        if (stakeholders_.empty()) {
            errors.push_back("Stakeholders are missing.");
        }

        if (acceptanceCriteria_.empty()) {
            errors.push_back("Acceptance criteria are missing.");
        }

        if (!isfinite(budgetCeiling_) || budgetCeiling_ <= 0.0) {
            errors.push_back("Budget ceiling must be greater than zero.");
        }

        return errors;
    }

    AuthorizationDecision evaluateAuthorization(
        const string& decisionMaker
    ) {
        const vector<string> errors = validate();

        if (!errors.empty()) {
            status_ = AuthorizationStatus::UnderReview;

            ostringstream reason;
            reason << "Validation failed: ";

            for (size_t i = 0; i < errors.size(); ++i) {
                if (i > 0) {
                    reason << "; ";
                }
                reason << errors[i];
            }

            return {
                Decision::RequestRevision,
                decisionMaker,
                reason.str()
            };
        }

        status_ = AuthorizationStatus::Authorized;

        return {
            Decision::Approve,
            decisionMaker,
            "Charter satisfies the minimum authorization requirements."
        };
    }

    void revise() {
        ++version_;
        status_ = AuthorizationStatus::Draft;
    }

    void reject() {
        status_ = AuthorizationStatus::Rejected;
    }

    AuthorizationStatus status() const {
        return status_;
    }

    int version() const {
        return version_;
    }

    double budgetCeiling() const {
        return budgetCeiling_;
    }

    const string& projectId() const {
        return projectId_;
    }

    const string& title() const {
        return title_;
    }

    const string& sponsor() const {
        return sponsor_;
    }

    const string& projectManager() const {
        return projectManager_;
    }

    const vector<Objective>& objectives() const {
        return objectives_;
    }

    const vector<string>& deliverables() const {
        return deliverables_;
    }

    const vector<Milestone>& milestones() const {
        return milestones_;
    }

    const vector<Risk>& risks() const {
        return risks_;
    }

    const vector<Stakeholder>& stakeholders() const {
        return stakeholders_;
    }
};


// -----------------------------------------------------------------------------
// 9. Risk register functions
// -----------------------------------------------------------------------------

vector<Risk> rankedRisks(const ProjectCharter& charter) {
    vector<Risk> result = charter.risks();

    // std::sort gives a practical O(n log n) ranking operation.
    sort(
        result.begin(),
        result.end(),
        [](const Risk& a, const Risk& b) {
            return a.exposure() > b.exposure();
        }
    );

    return result;
}


// -----------------------------------------------------------------------------
// 10. Governance workflow
// -----------------------------------------------------------------------------

AuthorizationDecision runGovernanceReview(
    ProjectCharter& charter,
    const string& reviewer
) {
    /*
     * Governance is intentionally separate from validation.
     *
     * Validation checks whether required information exists.
     * Governance determines whether the organization is willing to authorize
     * the proposed investment.
     *
     * In a real system, governance might also evaluate:
     *   - strategic priority
     *   - financial return
     *   - regulatory exposure
     *   - resource capacity
     *   - portfolio conflicts
     *   - risk appetite
     *   - architecture or security review
     */

    return charter.evaluateAuthorization(reviewer);
}


// -----------------------------------------------------------------------------
// 11. Build the case-study charter
// -----------------------------------------------------------------------------

ProjectCharter createCaseStudyCharter() {
    Objective objective{
        "Reduce average customer-support response time from 12 hours to "
        "4 hours within six months.",
        true,
        true,
        true,
        true,
        true
    };

    vector<Risk> risks{
        {
            "R-001",
            "Legacy customer-support data may be incomplete.",
            0.60,
            8.0,
            "Perform a data-quality assessment before implementation."
        },
        {
            "R-002",
            "Support employees may resist process changes.",
            0.50,
            7.0,
            "Conduct workshops, training, and pilot testing."
        },
        {
            "R-003",
            "Integration work may take longer than estimated.",
            0.40,
            9.0,
            "Prototype critical integrations early."
        }
    };

    vector<Stakeholder> stakeholders{
        {
            "Chief Customer Officer",
            "Executive Sponsor",
            5,
            5
        },
        {
            "Support Operations Lead",
            "Business Owner",
            5,
            5
        },
        {
            "Support Agents",
            "Users",
            3,
            5
        },
        {
            "Finance",
            "Control Function",
            4,
            3
        }
    };

    return ProjectCharter(
        "PRJ-CPP-001",
        "Customer Support Response Transformation",
        "Chief Customer Officer",
        "Project Delivery Manager",
        "Reduce customer waiting time and improve service quality.",
        "Long response times increase dissatisfaction, escalation volume, "
        "and operating cost.",
        {
            "Improve customer experience",
            "Reduce avoidable operating cost",
            "Increase service efficiency"
        },
        {objective},
        {
            "Support workflow redesign",
            "Response-time dashboard",
            "Notification rules",
            "Agent training"
        },
        {
            "Replacing the enterprise CRM",
            "Changing product pricing",
            "Redesigning unrelated sales workflows"
        },
        {
            "Approved process design",
            "Operational dashboard",
            "Notification mechanism",
            "Training package"
        },
        {
            {"Charter authorization", "2026-10-01"},
            {"Process design approved", "2026-11-01"},
            {"Pilot completed", "2026-12-15"},
            {"Production rollout", "2027-01-15"}
        },
        {
            "Business users will provide timely requirements.",
            "Existing support data is sufficiently usable.",
            "Required technical teams will be available."
        },
        {
            "Budget cannot exceed the approved ceiling.",
            "The existing CRM cannot be replaced.",
            "Customer disruption must be minimized."
        },
        move(risks),
        move(stakeholders),
        {
            "Response-time measurement is operational.",
            "Pilot users can execute the redesigned workflow.",
            "Dashboard results reconcile with source data.",
            "Sponsor accepts the final rollout package."
        },
        250000.0
    );
}


// -----------------------------------------------------------------------------
// 12. Main case study
// -----------------------------------------------------------------------------

int main() {
    try {
        section("PROJECT CHARTER: UNDERSTANDING PROJECT AUTHORIZATION");

        cout
            << "Scenario: A financial-services organization is considering "
            << "a customer-support transformation project.\n"
            << "The organization must decide whether the proposed project "
            << "is sufficiently defined and justified for authorization.\n";

        section("1. Project Authorization");

        ProjectCharter charter = createCaseStudyCharter();

        cout << "Project ID: " << charter.projectId() << "\n";
        cout << "Title: " << charter.title() << "\n";
        cout << "Sponsor: " << charter.sponsor() << "\n";
        cout << "Project Manager: " << charter.projectManager() << "\n";
        cout << "Initial status: " << toString(charter.status()) << "\n";

        AuthorizationDecision decision =
            runGovernanceReview(charter, "Executive Sponsor");

        cout << "\nDecision: " << toString(decision.decision) << "\n";
        cout << "Decision maker: " << decision.decisionMaker << "\n";
        cout << "Rationale: " << decision.rationale << "\n";
        cout << "Current status: " << toString(charter.status()) << "\n";


        section("2. Objective Analysis");

        for (const auto& objective : charter.objectives()) {
            cout << "Objective: " << objective.description << "\n";
            cout << "SMART score: " << objective.smartScore() << "/5\n";
            cout << "SMART: "
                 << (objective.isSMART() ? "Yes" : "No")
                 << "\n\n";
        }


        section("3. Deliverables and Milestones");

        cout << "Deliverables:\n";
        for (const auto& deliverable : charter.deliverables()) {
            cout << "  - " << deliverable << "\n";
        }

        cout << "\nMilestones:\n";
        for (const auto& milestone : charter.milestones()) {
            cout << "  - "
                 << milestone.name
                 << ": "
                 << milestone.targetDate
                 << "\n";
        }


        section("4. Risk Register");

        vector<Risk> ranked = rankedRisks(charter);

        cout << fixed << setprecision(2);

        for (const auto& risk : ranked) {
            cout
                << risk.id
                << " | "
                << risk.severity()
                << " | exposure="
                << risk.exposure()
                << " | "
                << risk.description
                << "\n";
        }

        /*
         * Why sort by exposure?
         *
         * A project team has limited attention. Ranking risk exposure creates
         * a rational mechanism for prioritizing governance attention.
         *
         * Complexity:
         *     O(R log R)
         *
         * where R is the number of risks.
         */


        section("5. Stakeholder Governance");

        for (const auto& stakeholder : charter.stakeholders()) {
            cout
                << stakeholder.name
                << " | role="
                << stakeholder.role
                << " | influence="
                << stakeholder.influence
                << " | interest="
                << stakeholder.interest
                << " | strategy="
                << stakeholder.engagementStrategy()
                << "\n";
        }


        section("6. Authorization as a Governance Decision");

        /*
         * A common conceptual mistake is treating the charter as the
         * authorization itself.
         *
         * The charter is the authorization document or basis for the
         * authorization decision.
         *
         * Authorization occurs when the appropriate authority explicitly
         * approves the project and grants permission to proceed.
         */

        if (decision.decision == Decision::Approve) {
            cout
                << "The project is authorized because the required "
                << "authorization information passed review.\n";
        }


        section("7. Change Request");

        ChangeRequest request{
            "CR-001",
            "Add a second customer-support channel.",
            "Support Operations Lead",
            "High",
            40000.0,
            20
        };

        cout << "Change request: " << request.description << "\n";
        cout << "Requested by: " << request.requestedBy << "\n";
        cout << "Budget impact: " << request.budgetImpact << "\n";
        cout << "Schedule impact: "
             << request.scheduleImpactDays
             << " days\n";
        cout << "Scope impact: " << request.scopeImpact << "\n";
        cout << "Governance review required: "
             << (request.requiresGovernanceReview() ? "Yes" : "No")
             << "\n";

        /*
         * A material change can invalidate assumptions behind the original
         * authorization. It may therefore require escalation, re-approval,
         * or a revised charter depending on organizational governance.
         */


        section("8. Charter Versioning");

        const int originalVersion = charter.version();

        charter.revise();

        cout
            << "Original version: "
            << originalVersion
            << "\n";

        cout
            << "After revision: "
            << charter.version()
            << "\n";

        cout
            << "Status after revision: "
            << toString(charter.status())
            << "\n";

        /*
         * Revision returns the charter to Draft in this simplified model.
         * The organization would then review the changed authorization basis.
         */

        decision = runGovernanceReview(charter, "Executive Sponsor");

        cout
            << "Post-revision decision: "
            << toString(decision.decision)
            << "\n";

        cout
            << "Post-revision status: "
            << toString(charter.status())
            << "\n";


        section("9. Edge Case: Invalid Charter");

        ProjectCharter invalid(
            "",
            "",
            "",
            "",
            "",
            "",
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            0.0
        );

        const auto errors = invalid.validate();

        cout << "Validation errors: " << errors.size() << "\n";

        for (const auto& error : errors) {
            cout << "  - " << error << "\n";
        }

        assert(!errors.empty());


        section("10. Business Case and Strategic Alignment");

        cout
            << "Authorization should consider more than whether a project "
            << "is technically possible.\n"
            << "\n"
            << "Important decision dimensions include:\n"
            << "  - Strategic alignment\n"
            << "  - Expected business value\n"
            << "  - Cost and funding capacity\n"
            << "  - Organizational capability\n"
            << "  - Risk exposure\n"
            << "  - Regulatory requirements\n"
            << "  - Resource availability\n"
            << "  - Portfolio priorities\n";


        section("11. Scope Boundary");

        cout
            << "In-scope examples:\n"
            << "  - Workflow redesign\n"
            << "  - Response-time measurement\n"
            << "  - Dashboard implementation\n"
            << "\n"
            << "Out-of-scope examples:\n"
            << "  - CRM replacement\n"
            << "  - Product pricing changes\n"
            << "  - Unrelated sales-process redesign\n";

        /*
         * Explicit exclusion is important because stakeholders often infer
         * scope from objectives. A boundary prevents a legitimate objective
         * from silently becoming an unlimited implementation request.
         */


        section("12. Complexity and Data Structures");

        cout
            << "Primary data structures:\n"
            << "  vector<Objective>      -> project objectives\n"
            << "  vector<Risk>           -> risk register\n"
            << "  vector<Stakeholder>    -> stakeholder register\n"
            << "  vector<Milestone>      -> milestone list\n"
            << "\n"
            << "Validation is approximately linear in the number of stored items.\n"
            << "Risk ranking uses sorting and is approximately O(R log R).\n"
            << "The computational cost is normally trivial for a single charter.\n"
            << "Governance complexity is generally more significant than CPU cost.\n";


        section("13. Production Design Considerations");

        cout
            << "A production authorization system should consider:\n"
            << "  - Authentication and role-based authorization\n"
            << "  - Immutable approval records\n"
            << "  - Audit logs\n"
            << "  - Version history\n"
            << "  - Digital signatures where legally required\n"
            << "  - Separation of duties\n"
            << "  - Conflict-of-interest controls\n"
            << "  - Financial approval thresholds\n"
            << "  - Regulatory retention requirements\n"
            << "  - Encryption for sensitive project information\n"
            << "  - Input validation and data integrity\n"
            << "  - Recovery and backup procedures\n";


        section("14. Security Considerations");

        cout
            << "Project charters can contain commercially sensitive information.\n"
            << "Potentially sensitive data includes budgets, strategic priorities,\n"
            << "customer-impact information, vendor information, and risk details.\n"
            << "\n"
            << "A production system should not assume that every stakeholder can\n"
            << "view every charter field. Access should be based on least privilege.\n";


        section("15. Complete Authorization Workflow");

        const vector<string> workflow{
            "Identify business problem or opportunity",
            "Develop business case",
            "Confirm strategic alignment",
            "Define high-level objectives",
            "Define scope boundaries",
            "Identify deliverables and milestones",
            "Identify sponsor and project manager",
            "Identify key stakeholders",
            "Document assumptions and constraints",
            "Identify material risks",
            "Define acceptance criteria",
            "Establish authorization-level funding",
            "Draft charter",
            "Conduct review",
            "Resolve material gaps",
            "Obtain formal approval",
            "Record decision and version",
            "Transition to detailed project planning"
        };

        for (size_t i = 0; i < workflow.size(); ++i) {
            cout
                << setw(2)
                << (i + 1)
                << ". "
                << workflow[i]
                << "\n";
        }


        section("16. Final Authorization State");

        cout
            << "Project: "
            << charter.title()
            << "\n"
            << "Project ID: "
            << charter.projectId()
            << "\n"
            << "Sponsor: "
            << charter.sponsor()
            << "\n"
            << "Project Manager: "
            << charter.projectManager()
            << "\n"
            << "Status: "
            << toString(charter.status())
            << "\n"
            << "Version: "
            << charter.version()
            << "\n"
            << "Budget ceiling: "
            << charter.budgetCeiling()
            << "\n";

        cout
            << "\nThe case study demonstrates the distinction between creating a "
            << "charter and authorizing a project. The charter establishes the "
            << "purpose, boundaries, objectives, stakeholders, risks, and "
            << "governance basis. The authorized decision grants organizational "
            << "permission to proceed.\n";

        return 0;
    }
    catch (const exception& error) {
        cerr << "Fatal error: " << error.what() << "\n";
        return 1;
    }
}
