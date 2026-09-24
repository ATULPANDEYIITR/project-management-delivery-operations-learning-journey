/*
 * Requirements Documentation
 * ===========================
 *
 * Industry-style C++17 case study:
 * Digital Service Request Management System
 *
 * The program demonstrates how requirements documentation can be transformed
 * into structured engineering artifacts and then checked for:
 *
 *   - requirement classification
 *   - stakeholder ownership
 *   - priority
 *   - acceptance criteria
 *   - validation
 *   - dependencies
 *   - traceability
 *   - authorization requirements
 *   - audit requirements
 *   - performance requirements
 *   - change management
 *   - quality metrics
 *
 * Compile:
 *   g++ -std=c++17 -O2 requirements_documentation.cpp -o requirements_documentation
 *
 * Run:
 *   ./requirements_documentation
 */

#include <algorithm>
#include <cassert>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;


// ---------------------------------------------------------------------------
// 1. Domain enumerations
// ---------------------------------------------------------------------------

enum class RequirementType {
    Business,
    User,
    Functional,
    NonFunctional,
    Data,
    Interface,
    Regulatory,
    Security
};

enum class Priority {
    Must,
    Should,
    Could,
    Wont
};

enum class RequirementStatus {
    Proposed,
    Approved,
    Implemented,
    Verified,
    Rejected
};

enum class ChangeStatus {
    Proposed,
    Analyzing,
    Approved,
    Rejected,
    Implemented
};


string toString(RequirementType type) {
    switch (type) {
        case RequirementType::Business: return "Business";
        case RequirementType::User: return "User";
        case RequirementType::Functional: return "Functional";
        case RequirementType::NonFunctional: return "Non-functional";
        case RequirementType::Data: return "Data";
        case RequirementType::Interface: return "Interface";
        case RequirementType::Regulatory: return "Regulatory";
        case RequirementType::Security: return "Security";
    }

    return "Unknown";
}


string toString(Priority priority) {
    switch (priority) {
        case Priority::Must: return "Must";
        case Priority::Should: return "Should";
        case Priority::Could: return "Could";
        case Priority::Wont: return "Won't";
    }

    return "Unknown";
}


string toString(RequirementStatus status) {
    switch (status) {
        case RequirementStatus::Proposed: return "Proposed";
        case RequirementStatus::Approved: return "Approved";
        case RequirementStatus::Implemented: return "Implemented";
        case RequirementStatus::Verified: return "Verified";
        case RequirementStatus::Rejected: return "Rejected";
    }

    return "Unknown";
}


string toString(ChangeStatus status) {
    switch (status) {
        case ChangeStatus::Proposed: return "Proposed";
        case ChangeStatus::Analyzing: return "Analyzing";
        case ChangeStatus::Approved: return "Approved";
        case ChangeStatus::Rejected: return "Rejected";
        case ChangeStatus::Implemented: return "Implemented";
    }

    return "Unknown";
}


// ---------------------------------------------------------------------------
// 2. Acceptance criteria
// ---------------------------------------------------------------------------

struct AcceptanceCriterion {
    string id;
    string condition;
    string behavior;
    string expectedResult;
    bool testable = true;

    vector<string> validate() const {
        vector<string> errors;

        if (id.empty()) {
            errors.push_back("Missing acceptance criterion ID.");
        }

        if (condition.empty()) {
            errors.push_back("Missing acceptance criterion condition.");
        }

        if (behavior.empty()) {
            errors.push_back("Missing acceptance criterion behavior.");
        }

        if (expectedResult.empty()) {
            errors.push_back("Missing expected result.");
        }

        return errors;
    }
};


// ---------------------------------------------------------------------------
// 3. Stakeholder model
// ---------------------------------------------------------------------------

struct Stakeholder {
    string id;
    string name;
    string role;
    int influence;
    int interest;

    int impactScore() const {
        return influence * interest;
    }
};


// ---------------------------------------------------------------------------
// 4. Requirement model
// ---------------------------------------------------------------------------

struct Requirement {
    string id;
    string title;
    string description;

    RequirementType type;
    Priority priority;
    RequirementStatus status;

    string source;
    string rationale;
    string owner;

    vector<AcceptanceCriterion> acceptanceCriteria;

    set<string> stakeholderIds;
    set<string> dependencies;
    set<string> relatedRequirements;
    set<string> tags;

    vector<string> assumptions;
    vector<string> constraints;
    vector<string> risks;

    int version = 1;

    bool isVerifiable() const {
        if (acceptanceCriteria.empty()) {
            return false;
        }

        return all_of(
            acceptanceCriteria.begin(),
            acceptanceCriteria.end(),
            [](const AcceptanceCriterion& criterion) {
                return criterion.testable;
            }
        );
    }

    vector<string> validate() const {
        vector<string> errors;

        if (id.empty()) {
            errors.push_back("Missing requirement ID.");
        }

        if (title.empty()) {
            errors.push_back("Missing requirement title.");
        }

        if (description.empty()) {
            errors.push_back("Missing description.");
        }

        if (description.size() < 30) {
            errors.push_back("Description may be too short.");
        }

        // Requirements that express system behavior or measurable qualities
        // should normally have explicit verification conditions.
        if (
            (type == RequirementType::Functional ||
             type == RequirementType::NonFunctional ||
             type == RequirementType::Security)
            && acceptanceCriteria.empty()
        ) {
            errors.push_back("Requirement has no acceptance criteria.");
        }

        if (source.empty()) {
            errors.push_back("Missing requirement source.");
        }

        if (rationale.empty()) {
            errors.push_back("Missing requirement rationale.");
        }

        for (const auto& criterion : acceptanceCriteria) {
            const auto criterionErrors = criterion.validate();

            for (const auto& error : criterionErrors) {
                errors.push_back(criterion.id + ": " + error);
            }
        }

        return errors;
    }
};


// ---------------------------------------------------------------------------
// 5. Change request
// ---------------------------------------------------------------------------

struct ChangeRequest {
    string id;
    string requirementId;
    string requestedBy;
    string description;
    string businessReason;
    string impact;

    ChangeStatus status = ChangeStatus::Proposed;

    int oldVersion = 1;
    int newVersion = 0;

    void approve(int currentVersion) {
        status = ChangeStatus::Approved;
        oldVersion = currentVersion;
        newVersion = currentVersion + 1;
    }
};


// ---------------------------------------------------------------------------
// 6. Requirements repository
// ---------------------------------------------------------------------------

class RequirementsRepository {
private:
    map<string, Requirement> requirements;
    map<string, Stakeholder> stakeholders;
    map<string, ChangeRequest> changes;

public:
    void addStakeholder(const Stakeholder& stakeholder) {
        if (stakeholders.count(stakeholder.id)) {
            throw runtime_error(
                "Duplicate stakeholder ID: " + stakeholder.id
            );
        }

        stakeholders[stakeholder.id] = stakeholder;
    }

    void addRequirement(const Requirement& requirement) {
        if (requirements.count(requirement.id)) {
            throw runtime_error(
                "Duplicate requirement ID: " + requirement.id
            );
        }

        for (const auto& stakeholderId : requirement.stakeholderIds) {
            if (!stakeholders.count(stakeholderId)) {
                throw runtime_error(
                    "Unknown stakeholder ID: " + stakeholderId
                );
            }
        }

        requirements[requirement.id] = requirement;
    }

    Requirement& getRequirement(const string& id) {
        auto iterator = requirements.find(id);

        if (iterator == requirements.end()) {
            throw runtime_error(
                "Requirement not found: " + id
            );
        }

        return iterator->second;
    }

    const map<string, Requirement>& allRequirements() const {
        return requirements;
    }

    const map<string, Stakeholder>& allStakeholders() const {
        return stakeholders;
    }

    void registerChange(const ChangeRequest& change) {
        if (changes.count(change.id)) {
            throw runtime_error(
                "Duplicate change ID: " + change.id
            );
        }

        if (!requirements.count(change.requirementId)) {
            throw runtime_error(
                "Cannot change unknown requirement: " +
                change.requirementId
            );
        }

        changes[change.id] = change;
    }

    vector<Requirement> search(const string& query) const {
        vector<Requirement> results;

        for (const auto& [id, requirement] : requirements) {
            if (
                id.find(query) != string::npos ||
                requirement.title.find(query) != string::npos ||
                requirement.description.find(query) != string::npos
            ) {
                results.push_back(requirement);
            }
        }

        return results;
    }
};


// ---------------------------------------------------------------------------
// 7. Traceability matrix
// ---------------------------------------------------------------------------

class TraceabilityMatrix {
private:
    map<string, set<string>> requirementToDesign;
    map<string, set<string>> requirementToCode;
    map<string, set<string>> requirementToTests;

public:
    void linkDesign(
        const string& requirementId,
        const string& designId
    ) {
        requirementToDesign[requirementId].insert(designId);
    }

    void linkCode(
        const string& requirementId,
        const string& codeId
    ) {
        requirementToCode[requirementId].insert(codeId);
    }

    void linkTest(
        const string& requirementId,
        const string& testId
    ) {
        requirementToTests[requirementId].insert(testId);
    }

    bool hasDesign(const string& id) const {
        auto iterator = requirementToDesign.find(id);

        return iterator != requirementToDesign.end()
            && !iterator->second.empty();
    }

    bool hasCode(const string& id) const {
        auto iterator = requirementToCode.find(id);

        return iterator != requirementToCode.end()
            && !iterator->second.empty();
    }

    bool hasTests(const string& id) const {
        auto iterator = requirementToTests.find(id);

        return iterator != requirementToTests.end()
            && !iterator->second.empty();
    }

    struct Coverage {
        double design = 0.0;
        double code = 0.0;
        double tests = 0.0;
        double complete = 0.0;
    };

    Coverage calculate(
        const map<string, Requirement>& requirements
    ) const {
        Coverage coverage;

        if (requirements.empty()) {
            return coverage;
        }

        double total = static_cast<double>(requirements.size());

        for (const auto& [id, requirement] : requirements) {
            bool design = hasDesign(id);
            bool code = hasCode(id);
            bool tests = hasTests(id);

            coverage.design += design ? 1.0 : 0.0;
            coverage.code += code ? 1.0 : 0.0;
            coverage.tests += tests ? 1.0 : 0.0;
            coverage.complete +=
                (design && code && tests) ? 1.0 : 0.0;
        }

        coverage.design = coverage.design / total * 100.0;
        coverage.code = coverage.code / total * 100.0;
        coverage.tests = coverage.tests / total * 100.0;
        coverage.complete = coverage.complete / total * 100.0;

        return coverage;
    }
};


// ---------------------------------------------------------------------------
// 8. Requirements analyzer
// ---------------------------------------------------------------------------

class RequirementsAnalyzer {
public:
    static map<Priority, int> priorityDistribution(
        const map<string, Requirement>& requirements
    ) {
        map<Priority, int> distribution = {
            {Priority::Must, 0},
            {Priority::Should, 0},
            {Priority::Could, 0},
            {Priority::Wont, 0}
        };

        for (const auto& [id, requirement] : requirements) {
            distribution[requirement.priority]++;
        }

        return distribution;
    }

    static int validationErrorCount(
        const map<string, Requirement>& requirements
    ) {
        int total = 0;

        for (const auto& [id, requirement] : requirements) {
            total += static_cast<int>(
                requirement.validate().size()
            );
        }

        return total;
    }

    static bool hasCircularDependency(
        const map<string, Requirement>& requirements
    ) {
        enum class State {
            Unvisited,
            Visiting,
            Complete
        };

        map<string, State> state;

        for (const auto& [id, requirement] : requirements) {
            state[id] = State::Unvisited;
        }

        function<bool(const string&)> visit =
            [&](const string& current) -> bool {
                if (state[current] == State::Visiting) {
                    return true;
                }

                if (state[current] == State::Complete) {
                    return false;
                }

                state[current] = State::Visiting;

                for (const auto& dependency :
                     requirements.at(current).dependencies) {

                    if (!requirements.count(dependency)) {
                        continue;
                    }

                    if (visit(dependency)) {
                        return true;
                    }
                }

                state[current] = State::Complete;
                return false;
            };

        for (const auto& [id, requirement] : requirements) {
            if (visit(id)) {
                return true;
            }
        }

        return false;
    }
};


// ---------------------------------------------------------------------------
// 9. Requirement-document generation
// ---------------------------------------------------------------------------

class RequirementsDocumentGenerator {
public:
    static string generate(
        const RequirementsRepository& repository,
        const TraceabilityMatrix& traceability
    ) {
        ostringstream document;

        document
            << "# Digital Service Request Platform\n\n"
            << "## Requirements Specification\n\n";

        document
            << "| ID | Type | Priority | Status | Title |\n"
            << "|---|---|---|---|---|\n";

        for (const auto& [id, requirement] :
             repository.allRequirements()) {

            document
                << "| " << id
                << " | " << toString(requirement.type)
                << " | " << toString(requirement.priority)
                << " | " << toString(requirement.status)
                << " | " << requirement.title
                << " |\n";
        }

        document << "\n## Detailed Requirements\n\n";

        for (const auto& [id, requirement] :
             repository.allRequirements()) {

            document
                << "### " << id << ": "
                << requirement.title << "\n\n";

            document
                << "**Description:** "
                << requirement.description << "\n\n";

            document
                << "**Source:** "
                << requirement.source << "\n\n";

            document
                << "**Rationale:** "
                << requirement.rationale << "\n\n";

            document << "**Acceptance criteria:**\n\n";

            for (const auto& criterion :
                 requirement.acceptanceCriteria) {

                document
                    << "- " << criterion.id
                    << ": Given " << criterion.condition
                    << ", when " << criterion.behavior
                    << ", then "
                    << criterion.expectedResult
                    << ".\n";
            }
        }

        document
            << "\n## Traceability\n\n"
            << "| Requirement | Design | Code | Tests |\n"
            << "|---|---|---|---|\n";

        for (const auto& [id, requirement] :
             repository.allRequirements()) {

            document
                << "| " << id
                << " | "
                << (traceability.hasDesign(id) ? "Linked" : "Missing")
                << " | "
                << (traceability.hasCode(id) ? "Linked" : "Missing")
                << " | "
                << (traceability.hasTests(id) ? "Linked" : "Missing")
                << " |\n";
        }

        return document.str();
    }
};


// ---------------------------------------------------------------------------
// 10. Case-study construction helpers
// ---------------------------------------------------------------------------

AcceptanceCriterion criterion(
    const string& id,
    const string& condition,
    const string& behavior,
    const string& expectedResult
) {
    return AcceptanceCriterion{
        id,
        condition,
        behavior,
        expectedResult,
        true
    };
}


void addStakeholders(RequirementsRepository& repository) {
    repository.addStakeholder({
        "STK-001",
        "Service Customer",
        "Primary user",
        4,
        5
    });

    repository.addStakeholder({
        "STK-002",
        "Operations Manager",
        "Business owner",
        5,
        5
    });

    repository.addStakeholder({
        "STK-003",
        "Support Agent",
        "Operational user",
        4,
        4
    });

    repository.addStakeholder({
        "STK-004",
        "Security Officer",
        "Security governance",
        5,
        4
    });

    repository.addStakeholder({
        "STK-005",
        "Compliance Officer",
        "Regulatory governance",
        5,
        3
    });
}


RequirementsRepository buildRequirements() {
    RequirementsRepository repository;
    addStakeholders(repository);

    repository.addRequirement({
        "BR-001",
        "Digital service requests",
        "The platform shall provide a digital channel for customers "
        "to submit service requests without contacting an agent.",
        RequirementType::Business,
        Priority::Must,
        RequirementStatus::Approved,
        "Operations workshop",
        "The organization wants to reduce manual request handling "
        "and provide a measurable digital service channel.",
        "Operations Manager",
        {},
        {"STK-001", "STK-002"},
        {},
        {},
        {"business", "digital-service"},
        {},
        {},
        {},
        1
    });

    repository.addRequirement({
        "FR-001",
        "Create a service request",
        "The system shall allow an authenticated customer to create "
        "a service request by selecting a category, entering a "
        "description, and submitting the request.",
        RequirementType::Functional,
        Priority::Must,
        RequirementStatus::Approved,
        "Customer interview",
        "Request creation is the primary customer workflow.",
        "Product Owner",
        {
            criterion(
                "AC-001",
                "the customer is authenticated",
                "the customer provides a valid category and description",
                "a unique request ID is created and displayed"
            ),
            criterion(
                "AC-002",
                "the description is empty",
                "the customer attempts submission",
                "the request is rejected with a validation message"
            )
        },
        {"STK-001", "STK-002"},
        {"BR-001"},
        {},
        {"customer", "request", "core"},
        {},
        {},
        {},
        1
    });

    repository.addRequirement({
        "FR-002",
        "Track request status",
        "The system shall allow customers to view the current "
        "status and status history of their submitted requests.",
        RequirementType::Functional,
        Priority::Must,
        RequirementStatus::Approved,
        "Customer interview",
        "Customers need visibility into progress after submission.",
        "Product Owner",
        {
            criterion(
                "AC-003",
                "the customer owns the request",
                "the customer opens the request details",
                "the current status and chronological status history are shown"
            )
        },
        {"STK-001", "STK-003"},
        {"FR-001"},
        {},
        {"customer", "tracking"},
        {},
        {},
        {},
        1
    });

    repository.addRequirement({
        "FR-003",
        "Agent request queue",
        "The system shall provide authorized support agents with "
        "a queue containing requests assigned to their operational team.",
        RequirementType::Functional,
        Priority::Must,
        RequirementStatus::Approved,
        "Operations workshop",
        "Agents require a controlled operational work queue.",
        "Operations Manager",
        {
            criterion(
                "AC-004",
                "the user has the support-agent role",
                "the user opens the request queue",
                "only requests accessible to that operational team are shown"
            )
        },
        {"STK-002", "STK-003"},
        {"FR-001"},
        {},
        {"agent", "operations"},
        {},
        {},
        {},
        1
    });

    repository.addRequirement({
        "NFR-001",
        "Request response time",
        "The service shall return a successful request-status query "
        "within 2 seconds for at least 95 percent of requests under "
        "the defined normal operating load.",
        RequirementType::NonFunctional,
        Priority::Should,
        RequirementStatus::Approved,
        "Performance workshop",
        "Response-time expectations affect customer usability.",
        "Engineering",
        {
            criterion(
                "AC-005",
                "the system is under normal operating load",
                "1000 status queries are executed",
                "at least 950 complete within 2 seconds"
            )
        },
        {"STK-001", "STK-002"},
        {},
        {},
        {"performance", "latency"},
        {},
        {
            "Normal operating load must be defined before performance testing."
        },
        {},
        1
    });

    repository.addRequirement({
        "SEC-001",
        "Role-based access control",
        "The system shall enforce role-based authorization so that "
        "customers, support agents, managers, and administrators can "
        "access only operations permitted for their roles.",
        RequirementType::Security,
        Priority::Must,
        RequirementStatus::Approved,
        "Security architecture review",
        "Authorization prevents unauthorized access to service data.",
        "Security Officer",
        {
            criterion(
                "AC-006",
                "a customer attempts to access another customer's request",
                "the authorization check executes",
                "access is denied and the event is recorded"
            ),
            criterion(
                "AC-007",
                "an agent accesses an authorized team request",
                "the authorization check executes",
                "the request is displayed"
            )
        },
        {"STK-004", "STK-003"},
        {"FR-001"},
        {},
        {"security", "authorization"},
        {},
        {},
        {
            "Incorrect authorization rules could expose customer information."
        },
        1
    });

    repository.addRequirement({
        "DATA-001",
        "Request audit history",
        "The system shall record creation, assignment, status changes, "
        "and closure events for each service request with event time, "
        "actor identifier, and event type.",
        RequirementType::Data,
        Priority::Must,
        RequirementStatus::Approved,
        "Compliance workshop",
        "Auditable history supports accountability and investigation.",
        "Compliance Officer",
        {
            criterion(
                "AC-008",
                "a request status changes",
                "the transaction completes",
                "an immutable audit event exists with actor and timestamp"
            )
        },
        {"STK-005", "STK-004"},
        {"FR-001"},
        {},
        {"audit", "compliance", "data"},
        {},
        {
            "Audit records must not be editable through normal application operations."
        },
        {},
        1
    });

    return repository;
}


// ---------------------------------------------------------------------------
// 11. Build traceability
// ---------------------------------------------------------------------------

TraceabilityMatrix buildTraceability() {
    TraceabilityMatrix matrix;

    matrix.linkDesign("BR-001", "ARCH-001");
    matrix.linkDesign("FR-001", "DESIGN-REQ-API");
    matrix.linkDesign("FR-002", "DESIGN-REQUEST-VIEW");
    matrix.linkDesign("FR-003", "DESIGN-AGENT-QUEUE");
    matrix.linkDesign("NFR-001", "DESIGN-PERFORMANCE");
    matrix.linkDesign("SEC-001", "DESIGN-AUTHZ");
    matrix.linkDesign("DATA-001", "DESIGN-AUDIT");

    matrix.linkCode("FR-001", "RequestService.create");
    matrix.linkCode("FR-002", "RequestService.getStatus");
    matrix.linkCode("FR-003", "AgentQueue.list");
    matrix.linkCode("SEC-001", "AuthorizationPolicy");
    matrix.linkCode("DATA-001", "AuditRepository");

    matrix.linkTest("FR-001", "TEST-REQ-CREATE-001");
    matrix.linkTest("FR-002", "TEST-REQ-STATUS-001");
    matrix.linkTest("FR-003", "TEST-QUEUE-001");
    matrix.linkTest("NFR-001", "TEST-PERF-001");
    matrix.linkTest("SEC-001", "TEST-AUTHZ-001");
    matrix.linkTest("DATA-001", "TEST-AUDIT-001");

    return matrix;
}


// ---------------------------------------------------------------------------
// 12. Simulated domain system
// ---------------------------------------------------------------------------

enum class RequestStatus {
    Submitted,
    Assigned,
    InProgress,
    Resolved,
    Closed
};


string toString(RequestStatus status) {
    switch (status) {
        case RequestStatus::Submitted: return "Submitted";
        case RequestStatus::Assigned: return "Assigned";
        case RequestStatus::InProgress: return "In Progress";
        case RequestStatus::Resolved: return "Resolved";
        case RequestStatus::Closed: return "Closed";
    }

    return "Unknown";
}


struct ServiceRequest {
    string requestId;
    string customerId;
    string category;
    string description;
    RequestStatus status = RequestStatus::Submitted;
};


class AuthorizationPolicy {
public:
    static bool canViewRequest(
        const string& userId,
        const string& userRole,
        const ServiceRequest& request
    ) {
        // Security requirement is enforced before data is returned.
        if (userRole == "Administrator") {
            return true;
        }

        if (userRole == "Customer") {
            return userId == request.customerId;
        }

        if (userRole == "Agent") {
            // A real system would use team membership and request ownership.
            // This case study models the role boundary explicitly.
            return true;
        }

        return false;
    }
};


class RequestService {
private:
    vector<ServiceRequest> requests;
    int nextNumber = 1000;

public:
    ServiceRequest create(
        const string& customerId,
        const string& category,
        const string& description
    ) {
        // Input validation is part of translating a functional requirement
        // into observable system behavior.
        if (customerId.empty()) {
            throw invalid_argument("Customer ID is required.");
        }

        if (category.empty()) {
            throw invalid_argument("Category is required.");
        }

        if (description.empty()) {
            throw invalid_argument("Description is required.");
        }

        ServiceRequest request{
            "REQ-" + to_string(nextNumber++),
            customerId,
            category,
            description,
            RequestStatus::Submitted
        };

        requests.push_back(request);
        return request;
    }

    ServiceRequest getRequest(
        const string& userId,
        const string& userRole,
        const string& requestId
    ) const {
        auto iterator = find_if(
            requests.begin(),
            requests.end(),
            [&](const ServiceRequest& request) {
                return request.requestId == requestId;
            }
        );

        if (iterator == requests.end()) {
            throw out_of_range("Request not found.");
        }

        if (
            !AuthorizationPolicy::canViewRequest(
                userId,
                userRole,
                *iterator
            )
        ) {
            throw runtime_error(
                "Authorization failed."
            );
        }

        return *iterator;
    }

    void updateStatus(
        const string& requestId,
        RequestStatus newStatus
    ) {
        auto iterator = find_if(
            requests.begin(),
            requests.end(),
            [&](ServiceRequest& request) {
                return request.requestId == requestId;
            }
        );

        if (iterator == requests.end()) {
            throw out_of_range("Request not found.");
        }

        iterator->status = newStatus;
    }

    size_t size() const {
        return requests.size();
    }
};


// ---------------------------------------------------------------------------
// 13. Audit logging
// ---------------------------------------------------------------------------

struct AuditEvent {
    string requestId;
    string actorId;
    string eventType;
    string timestamp;
};


class AuditRepository {
private:
    vector<AuditEvent> events;

public:
    void append(
        const string& requestId,
        const string& actorId,
        const string& eventType,
        const string& timestamp
    ) {
        // append-only behavior models the documented audit requirement.
        events.push_back({
            requestId,
            actorId,
            eventType,
            timestamp
        });
    }

    const vector<AuditEvent>& all() const {
        return events;
    }
};


// ---------------------------------------------------------------------------
// 14. Test and verification helpers
// ---------------------------------------------------------------------------

void testRequestCreation() {
    RequestService service;

    ServiceRequest request = service.create(
        "CUSTOMER-1",
        "Billing",
        "Invoice amount is incorrect."
    );

    assert(request.requestId == "REQ-1000");
    assert(request.status == RequestStatus::Submitted);
    assert(service.size() == 1);
}


void testValidationFailure() {
    RequestService service;

    bool failed = false;

    try {
        service.create(
            "CUSTOMER-1",
            "Billing",
            ""
        );
    }
    catch (const invalid_argument&) {
        failed = true;
    }

    assert(failed);
}


void testAuthorization() {
    RequestService service;

    ServiceRequest request = service.create(
        "CUSTOMER-1",
        "Account",
        "Please update my account."
    );

    bool unauthorized = false;

    try {
        service.getRequest(
            "CUSTOMER-2",
            "Customer",
            request.requestId
        );
    }
    catch (const runtime_error&) {
        unauthorized = true;
    }

    assert(unauthorized);

    ServiceRequest authorized =
        service.getRequest(
            "CUSTOMER-1",
            "Customer",
            request.requestId
        );

    assert(authorized.customerId == "CUSTOMER-1");
}


void testAuditHistory() {
    AuditRepository repository;

    repository.append(
        "REQ-1000",
        "CUSTOMER-1",
        "CREATED",
        "2026-09-24T10:00:00"
    );

    repository.append(
        "REQ-1000",
        "AGENT-1",
        "STATUS_CHANGED",
        "2026-09-24T10:05:00"
    );

    assert(repository.all().size() == 2);
}


// ---------------------------------------------------------------------------
// 15. Console presentation
// ---------------------------------------------------------------------------

void printHeader(const string& title) {
    cout << "\n" << string(78, '=') << "\n";
    cout << title << "\n";
    cout << string(78, '=') << "\n";
}


void demonstrateRequirements(
    const RequirementsRepository& repository
) {
    printHeader("REQUIREMENT REGISTER");

    cout
        << left
        << setw(12) << "ID"
        << setw(18) << "TYPE"
        << setw(10) << "PRIORITY"
        << setw(12) << "STATUS"
        << "TITLE\n";

    cout << string(78, '-') << "\n";

    for (const auto& [id, requirement] :
         repository.allRequirements()) {

        cout
            << left
            << setw(12) << id
            << setw(18) << toString(requirement.type)
            << setw(10) << toString(requirement.priority)
            << setw(12) << toString(requirement.status)
            << requirement.title
            << "\n";
    }
}


void demonstrateValidation(
    const RequirementsRepository& repository
) {
    printHeader("REQUIREMENT VALIDATION");

    int totalErrors = 0;

    for (const auto& [id, requirement] :
         repository.allRequirements()) {

        const auto errors = requirement.validate();

        cout
            << id
            << " -> "
            << (errors.empty() ? "PASS" : "REVIEW")
            << "\n";

        for (const auto& error : errors) {
            cout << "    - " << error << "\n";
        }

        totalErrors += static_cast<int>(errors.size());
    }

    cout
        << "\nTotal automated validation findings: "
        << totalErrors
        << "\n";
}


void demonstrateStakeholders(
    const RequirementsRepository& repository
) {
    printHeader("STAKEHOLDER ANALYSIS");

    vector<Stakeholder> stakeholders;

    for (const auto& [id, stakeholder] :
         repository.allStakeholders()) {
        stakeholders.push_back(stakeholder);
    }

    sort(
        stakeholders.begin(),
        stakeholders.end(),
        [](const Stakeholder& a, const Stakeholder& b) {
            return a.impactScore() > b.impactScore();
        }
    );

    for (const auto& stakeholder : stakeholders) {
        cout
            << left
            << setw(25) << stakeholder.name
            << " influence=" << stakeholder.influence
            << ", interest=" << stakeholder.interest
            << ", score=" << stakeholder.impactScore()
            << "\n";
    }
}


void demonstrateTraceability(
    const RequirementsRepository& repository,
    const TraceabilityMatrix& matrix
) {
    printHeader("TRACEABILITY COVERAGE");

    const auto coverage =
        matrix.calculate(repository.allRequirements());

    cout << fixed << setprecision(1);
    cout << "Design coverage:   " << coverage.design << "%\n";
    cout << "Code coverage:     " << coverage.code << "%\n";
    cout << "Test coverage:     " << coverage.tests << "%\n";
    cout << "Complete coverage: " << coverage.complete << "%\n";

    cout
        << "\nTraceability is stronger when each approved requirement "
        << "has explicit links to design, implementation, and verification.\n";
}


void demonstrateDomainSystem() {
    printHeader("DOMAIN SYSTEM CASE STUDY");

    RequestService service;
    AuditRepository audit;

    ServiceRequest request = service.create(
        "CUSTOMER-101",
        "Billing",
        "The customer reports an incorrect invoice amount."
    );

    audit.append(
        request.requestId,
        "CUSTOMER-101",
        "CREATED",
        "2026-09-24T10:00:00"
    );

    service.updateStatus(
        request.requestId,
        RequestStatus::Assigned
    );

    audit.append(
        request.requestId,
        "AGENT-7",
        "STATUS_CHANGED",
        "2026-09-24T10:02:00"
    );

    ServiceRequest retrieved =
        service.getRequest(
            "CUSTOMER-101",
            "Customer",
            request.requestId
        );

    cout
        << "Request ID: "
        << retrieved.requestId
        << "\n";

    cout
        << "Category: "
        << retrieved.category
        << "\n";

    cout
        << "Status: "
        << toString(retrieved.status)
        << "\n";

    cout
        << "Audit events: "
        << audit.all().size()
        << "\n";

    // A second customer must not receive the first customer's request.
    try {
        service.getRequest(
            "CUSTOMER-999",
            "Customer",
            request.requestId
        );

        cout << "ERROR: unauthorized request was exposed.\n";
    }
    catch (const runtime_error& error) {
        cout
            << "Unauthorized access correctly rejected: "
            << error.what()
            << "\n";
    }
}


void demonstrateChangeControl(
    RequirementsRepository& repository
) {
    printHeader("CHANGE CONTROL");

    ChangeRequest change{
        "CR-001",
        "FR-002",
        "Operations Manager",
        "Display estimated completion time with request status.",
        "Customers need more precise timing information.",
        "Requires API, business-rule, UI, and test changes.",
        ChangeStatus::Proposed,
        1,
        0
    };

    repository.registerChange(change);

    Requirement& requirement =
        repository.getRequirement(change.requirementId);

    change.approve(requirement.version);

    requirement.description =
        "The system shall allow customers to view the current "
        "status, status history, and estimated completion time "
        "of their submitted requests.";

    requirement.version = change.newVersion;

    cout
        << change.id
        << " -> "
        << toString(change.status)
        << "\n";

    cout
        << "Requirement version: "
        << change.oldVersion
        << " -> "
        << requirement.version
        << "\n";
}


// ---------------------------------------------------------------------------
// 16. Main
// ---------------------------------------------------------------------------

int main() {
    try {
        printHeader("REQUIREMENTS DOCUMENTATION CASE STUDY");

        cout
            << "Scenario: a digital platform for customer service requests.\n"
            << "The implementation demonstrates how documented requirements "
            << "connect business needs to software behavior and verification.\n";

        RequirementsRepository repository =
            buildRequirements();

        TraceabilityMatrix traceability =
            buildTraceability();

        demonstrateRequirements(repository);
        demonstrateValidation(repository);
        demonstrateStakeholders(repository);
        demonstrateTraceability(repository, traceability);
        demonstrateDomainSystem();
        demonstrateChangeControl(repository);

        printHeader("GENERATED REQUIREMENTS DOCUMENT");

        const string document =
            RequirementsDocumentGenerator::generate(
                repository,
                traceability
            );

        // The complete generated document exists in memory. Only the first
        // portion is printed to keep terminal output manageable.
        istringstream stream(document);
        string line;
        int lineCount = 0;

        while (getline(stream, line) && lineCount < 30) {
            cout << line << "\n";
            ++lineCount;
        }

        cout
            << "\n[Generated document display truncated.]\n";

        printHeader("REQUIREMENT METRICS");

        auto distribution =
            RequirementsAnalyzer::priorityDistribution(
                repository.allRequirements()
            );

        for (const auto& [priority, count] : distribution) {
            cout
                << setw(10)
                << toString(priority)
                << ": "
                << count
                << "\n";
        }

        cout
            << "\nValidation findings: "
            << RequirementsAnalyzer::validationErrorCount(
                repository.allRequirements()
            )
            << "\n";

        cout
            << "Circular dependency detected: "
            << (
                RequirementsAnalyzer::hasCircularDependency(
                    repository.allRequirements()
                )
                ? "yes"
                : "no"
            )
            << "\n";

        printHeader("SELF-TESTS");

        testRequestCreation();
        testValidationFailure();
        testAuthorization();
        testAuditHistory();

        cout
            << "Request creation test: PASS\n"
            << "Validation failure test: PASS\n"
            << "Authorization test: PASS\n"
            << "Audit history test: PASS\n";

        printHeader("ENGINEERING DISTINCTIONS");

        cout
            << "Business requirement -> organizational outcome or reason\n"
            << "User requirement     -> user need or goal\n"
            << "Functional requirement -> required system behavior\n"
            << "Non-functional requirement -> measurable quality or constraint\n"
            << "Acceptance criterion -> condition for determining satisfaction\n"
            << "Validation -> suitability and quality of the requirement\n"
            << "Verification -> evidence that implementation satisfies it\n"
            << "Traceability -> lifecycle relationships between artifacts\n"
            << "Change control -> controlled evolution of an approved baseline\n";

        return 0;
    }
    catch (const exception& error) {
        cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return 1;
    }
}
