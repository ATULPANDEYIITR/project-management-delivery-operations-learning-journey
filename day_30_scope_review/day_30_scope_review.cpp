/*
 * Scope Review: Repository Governance and Scope Management
 *
 * C++17 case study:
 *
 * A release-governance service receives proposed repository changes and
 * evaluates whether the requested work belongs to an approved scope
 * baseline. The engine identifies scope mismatches, exclusions, material
 * effort changes, and unmapped work before a governance decision is recorded.
 *
 * This is intentionally different from a compiler, Git client, or code
 * review implementation. The system models the governance question:
 *
 *     "Does the requested change remain within the approved scope?"
 *
 * It demonstrates:
 * - immutable-style baseline records
 * - scope-item lookup with unordered_map
 * - explicit review state
 * - finding severity
 * - validation and exceptions
 * - change-control classification
 * - audit history
 * - separation between analysis and final decision
 * - complexity considerations for lookup and reporting
 */

#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

enum class ScopeStatus {
    InScope,
    PartiallyInScope,
    OutOfScope,
    RequiresChangeControl
};

enum class FindingSeverity {
    Low,
    Medium,
    High,
    Critical
};

enum class ReviewDecision {
    Accept,
    AcceptWithNotes,
    ReviseScope,
    Reject
};

std::string toString(ScopeStatus status) {
    switch (status) {
        case ScopeStatus::InScope:
            return "in_scope";
        case ScopeStatus::PartiallyInScope:
            return "partially_in_scope";
        case ScopeStatus::OutOfScope:
            return "out_of_scope";
        case ScopeStatus::RequiresChangeControl:
            return "requires_change_control";
    }

    return "unknown";
}

std::string toString(FindingSeverity severity) {
    switch (severity) {
        case FindingSeverity::Low:
            return "low";
        case FindingSeverity::Medium:
            return "medium";
        case FindingSeverity::High:
            return "high";
        case FindingSeverity::Critical:
            return "critical";
    }

    return "unknown";
}

std::string toString(ReviewDecision decision) {
    switch (decision) {
        case ReviewDecision::Accept:
            return "accept";
        case ReviewDecision::AcceptWithNotes:
            return "accept_with_notes";
        case ReviewDecision::ReviseScope:
            return "revise_scope";
        case ReviewDecision::Reject:
            return "reject";
    }

    return "unknown";
}

struct ScopeItem {
    std::string id;
    std::string name;
    std::string description;
    std::vector<std::string> acceptanceCriteria;
    bool excluded = false;
};

struct ChangeRequest {
    std::string id;
    std::string title;
    std::string description;
    std::string requestedBy;
    std::vector<std::string> relatedScopeItems;
    double estimatedHours = 0.0;
    std::string businessJustification;
};

struct ScopeFinding {
    std::string id;
    FindingSeverity severity;
    std::string subject;
    std::string description;
    std::vector<std::string> affectedItems;
    std::string recommendation;
    bool resolved = false;
};

struct ScopeReview {
    ChangeRequest request;
    ScopeStatus status;
    std::vector<ScopeFinding> findings;
    std::vector<std::string> matchedItems;
    std::vector<std::string> unmatchedReferences;
    double estimatedScopeDeltaHours = 0.0;
    bool finalized = false;
    ReviewDecision decision = ReviewDecision::Reject;
    std::string reviewer;

    bool hasUnresolvedFindings() const {
        return std::any_of(
            findings.begin(),
            findings.end(),
            [](const ScopeFinding& finding) {
                return !finding.resolved;
            }
        );
    }
};

struct AuditEvent {
    std::string eventType;
    std::string requestId;
    std::string actor;
    std::string detail;
};

class ScopeBaseline {
public:
    ScopeBaseline(
        std::string repository,
        std::string version,
        std::string objective,
        std::vector<ScopeItem> items,
        std::vector<std::string> exclusions
    )
        : repository_(std::move(repository)),
          version_(std::move(version)),
          objective_(std::move(objective)),
          exclusions_(std::move(exclusions)) {

        if (repository_.empty()) {
            throw std::invalid_argument("Repository cannot be empty.");
        }

        if (version_.empty()) {
            throw std::invalid_argument("Scope version cannot be empty.");
        }

        if (objective_.empty()) {
            throw std::invalid_argument("Scope objective cannot be empty.");
        }

        if (items.empty()) {
            throw std::invalid_argument(
                "At least one scope item is required."
            );
        }

        for (const auto& item : items) {
            if (item.id.empty()) {
                throw std::invalid_argument(
                    "Every scope item requires an identifier."
                );
            }

            if (item.name.empty() || item.description.empty()) {
                throw std::invalid_argument(
                    "Every scope item requires descriptive content."
                );
            }

            if (item.acceptanceCriteria.empty()) {
                throw std::invalid_argument(
                    "Every scope item requires acceptance criteria."
                );
            }

            const auto [iterator, inserted] =
                items_.emplace(item.id, item);

            if (!inserted) {
                throw std::invalid_argument(
                    "Duplicate scope item: " + item.id
                );
            }
        }
    }

    const ScopeItem* find(const std::string& id) const {
        auto iterator = items_.find(id);

        if (iterator == items_.end()) {
            return nullptr;
        }

        return &iterator->second;
    }

    bool isApproved(const std::string& id) const {
        const ScopeItem* item = find(id);
        return item != nullptr && !item->excluded;
    }

    const std::string& repository() const {
        return repository_;
    }

    const std::string& version() const {
        return version_;
    }

private:
    std::string repository_;
    std::string version_;
    std::string objective_;
    std::unordered_map<std::string, ScopeItem> items_;
    std::vector<std::string> exclusions_;
};

class ScopeGovernanceEngine {
public:
    explicit ScopeGovernanceEngine(const ScopeBaseline& baseline)
        : baseline_(baseline) {}

    ScopeReview analyze(const ChangeRequest& request) {
        validateRequest(request);

        ScopeReview review;
        review.request = request;
        review.status = ScopeStatus::OutOfScope;
        review.estimatedScopeDeltaHours = request.estimatedHours;

        for (const auto& scopeId : request.relatedScopeItems) {
            const ScopeItem* item = baseline_.find(scopeId);

            if (item == nullptr) {
                review.unmatchedReferences.push_back(scopeId);

                review.findings.push_back({
                    makeFindingId(request.id, "UNKNOWN"),
                    FindingSeverity::Medium,
                    "Unknown scope reference",
                    "The request references a scope item that is absent "
                    "from the approved baseline.",
                    {},
                    "Map the request to an approved scope item or "
                    "submit a formal scope change."
                });

                continue;
            }

            if (item->excluded) {
                review.unmatchedReferences.push_back(scopeId);

                review.findings.push_back({
                    makeFindingId(request.id, "EXCLUDED"),
                    FindingSeverity::High,
                    "Excluded scope item",
                    "The requested work references an item explicitly "
                    "excluded from the release.",
                    {scopeId},
                    "Change the approved scope before treating the work "
                    "as baseline scope."
                });

                continue;
            }

            review.matchedItems.push_back(scopeId);
        }

        if (request.relatedScopeItems.empty()) {
            review.findings.push_back({
                makeFindingId(request.id, "UNMAPPED"),
                FindingSeverity::High,
                "Unmapped change",
                "No approved baseline item is associated with this request.",
                {},
                "Create a formal scope item or remove the requested work."
            });
        }

        if (containsExpansionSignal(request.description)) {
            review.findings.push_back({
                makeFindingId(request.id, "EXPANSION"),
                FindingSeverity::Medium,
                "Potential scope expansion",
                "The request contains language indicating additional "
                "or changed functionality.",
                review.matchedItems,
                "Compare the requested behavior with the baseline "
                "acceptance criteria."
            });
        }

        if (request.estimatedHours > 16.0) {
            review.findings.push_back({
                makeFindingId(request.id, "EFFORT"),
                FindingSeverity::Medium,
                "Material effort change",
                "The estimated work is large enough to require explicit "
                "scope assessment.",
                review.matchedItems,
                "Compare the effort against the approved delivery boundary."
            });
        }

        const bool hasMatchedItems = !review.matchedItems.empty();
        const bool hasUnmatchedItems = !review.unmatchedReferences.empty();
        const bool hasExpansion = hasFindingSubject(
            review,
            "Potential scope expansion"
        );

        if (hasMatchedItems && !hasUnmatchedItems && !hasExpansion) {
            review.status = ScopeStatus::InScope;
        } else if (hasMatchedItems) {
            review.status = ScopeStatus::PartiallyInScope;
        } else {
            review.status = ScopeStatus::OutOfScope;
        }

        if (
            review.status != ScopeStatus::InScope ||
            request.estimatedHours > 16.0
        ) {
            review.status = ScopeStatus::RequiresChangeControl;
        }

        audit_.push_back({
            "scope.reviewed",
            request.id,
            request.requestedBy,
            toString(review.status)
        });

        return review;
    }

    void resolveFinding(
        ScopeReview& review,
        const std::string& findingId
    ) {
        auto iterator = std::find_if(
            review.findings.begin(),
            review.findings.end(),
            [&](const ScopeFinding& finding) {
                return finding.id == findingId;
            }
        );

        if (iterator == review.findings.end()) {
            throw std::invalid_argument(
                "Finding does not exist: " + findingId
            );
        }

        iterator->resolved = true;

        audit_.push_back({
            "scope.finding_resolved",
            review.request.id,
            "scope-controller",
            findingId
        });
    }

    void finalize(
        ScopeReview& review,
        const std::string& reviewer,
        ReviewDecision decision
    ) {
        if (reviewer.empty()) {
            throw std::invalid_argument("Reviewer cannot be empty.");
        }

        if (
            decision == ReviewDecision::Accept &&
            review.hasUnresolvedFindings()
        ) {
            throw std::logic_error(
                "A review with unresolved findings cannot be accepted."
            );
        }

        review.finalized = true;
        review.decision = decision;
        review.reviewer = reviewer;

        audit_.push_back({
            "scope.decision_recorded",
            review.request.id,
            reviewer,
            toString(decision)
        });
    }

    const std::vector<AuditEvent>& auditLog() const {
        return audit_;
    }

    void printAuditLog() const {
        std::cout << "\nAudit Log\n";
        std::cout << "---------\n";

        for (const auto& event : audit_) {
            std::cout
                << event.eventType
                << " | request=" << event.requestId
                << " | actor=" << event.actor
                << " | " << event.detail
                << '\n';
        }
    }

private:
    const ScopeBaseline& baseline_;
    std::vector<AuditEvent> audit_;

    static std::string makeFindingId(
        const std::string& requestId,
        const std::string& suffix
    ) {
        return "F-" + requestId + "-" + suffix;
    }

    static bool containsExpansionSignal(const std::string& text) {
        static const std::vector<std::string> signals = {
            "new ",
            "redesign",
            "migration",
            "unrelated",
            "additional",
            "replace"
        };

        return std::any_of(
            signals.begin(),
            signals.end(),
            [&](const std::string& signal) {
                return text.find(signal) != std::string::npos;
            }
        );
    }

    static bool hasFindingSubject(
        const ScopeReview& review,
        const std::string& subject
    ) {
        return std::any_of(
            review.findings.begin(),
            review.findings.end(),
            [&](const ScopeFinding& finding) {
                return finding.subject == subject;
            }
        );
    }

    static void validateRequest(const ChangeRequest& request) {
        if (request.id.empty()) {
            throw std::invalid_argument(
                "Change request ID cannot be empty."
            );
        }

        if (request.title.empty()) {
            throw std::invalid_argument(
                "Change request title cannot be empty."
            );
        }

        if (request.description.empty()) {
            throw std::invalid_argument(
                "Change request description cannot be empty."
            );
        }

        if (request.requestedBy.empty()) {
            throw std::invalid_argument(
                "Requester identity cannot be empty."
            );
        }

        if (request.estimatedHours < 0.0) {
            throw std::invalid_argument(
                "Estimated hours cannot be negative."
            );
        }
    }
};

void printReview(const ScopeReview& review) {
    std::cout << "\nScope Review\n";
    std::cout << "------------\n";
    std::cout << "Request: " << review.request.id << '\n';
    std::cout << "Title: " << review.request.title << '\n';
    std::cout << "Status: " << toString(review.status) << '\n';
    std::cout << "Estimated delta: "
              << review.estimatedScopeDeltaHours
              << " hours\n";

    std::cout << "Matched items: ";

    if (review.matchedItems.empty()) {
        std::cout << "none";
    } else {
        for (std::size_t i = 0; i < review.matchedItems.size(); ++i) {
            if (i > 0) {
                std::cout << ", ";
            }

            std::cout << review.matchedItems[i];
        }
    }

    std::cout << '\n';

    std::cout << "Findings:\n";

    if (review.findings.empty()) {
        std::cout << "  none\n";
    }

    for (const auto& finding : review.findings) {
        std::cout
            << "  ["
            << toString(finding.severity)
            << "] "
            << finding.subject
            << " - "
            << finding.description
            << '\n';

        std::cout
            << "    Action: "
            << finding.recommendation
            << '\n';

        std::cout
            << "    Resolved: "
            << (finding.resolved ? "yes" : "no")
            << '\n';
    }
}

ScopeBaseline createBaseline() {
    return ScopeBaseline(
        "release-governance-portal",
        "2.3",
        "Control release scope using an approved baseline and "
        "traceable scope reviews.",
        {
            {
                "SCOPE-101",
                "Release scope dashboard",
                "Display approved release items and their state.",
                {
                    "Approved items are visible.",
                    "Items retain stable identifiers.",
                    "Reviewers can inspect scope state."
                },
                false
            },
            {
                "SCOPE-102",
                "Scope change register",
                "Record proposed changes to approved release scope.",
                {
                    "Requests have unique identifiers.",
                    "Requests contain business justification.",
                    "Requests can be evaluated against the baseline."
                },
                false
            },
            {
                "SCOPE-103",
                "Scope review findings",
                "Record discrepancies discovered during scope review.",
                {
                    "Findings identify affected scope.",
                    "Findings have severity.",
                    "Findings have resolution guidance."
                },
                false
            },
            {
                "SCOPE-104",
                "Mobile redesign",
                "Full mobile redesign reserved for a later release.",
                {
                    "No redesign is included in release 2.3."
                },
                true
            }
        },
        {
            "Full mobile redesign",
            "External billing migration",
            "Unrelated analytics replacement"
        }
    );
}

void runCaseStudy() {
    const ScopeBaseline baseline = createBaseline();
    ScopeGovernanceEngine engine(baseline);

    std::vector<ChangeRequest> requests = {
        {
            "CR-401",
            "Improve scope dashboard filtering",
            "Add filtering to the existing scope dashboard so reviewers "
            "can isolate high-priority approved items.",
            "release-manager",
            {"SCOPE-101"},
            6.0,
            "Make scope review faster without changing the release boundary."
        },
        {
            "CR-402",
            "Add mobile redesign",
            "Add a new mobile interface and redesign the existing workflow.",
            "product-team",
            {"SCOPE-101", "SCOPE-104"},
            24.0,
            "Improve mobile usability before release."
        },
        {
            "CR-403",
            "Introduce external billing",
            "Add a new external billing integration to the release.",
            "commercial-team",
            {},
            20.0,
            "Support a future commercial workflow."
        }
    };

    std::vector<ScopeReview> reviews;

    for (const auto& request : requests) {
        ScopeReview review = engine.analyze(request);
        printReview(review);
        reviews.push_back(std::move(review));
    }

    // The first request is accepted only after every finding has been
    // explicitly resolved. This prevents a governance decision from being
    // inferred merely from an in-scope classification.
    for (const auto& finding : reviews[0].findings) {
        engine.resolveFinding(reviews[0], finding.id);
    }

    engine.finalize(
        reviews[0],
        "scope-controller",
        ReviewDecision::Accept
    );

    engine.finalize(
        reviews[1],
        "scope-controller",
        ReviewDecision::ReviseScope
    );

    engine.finalize(
        reviews[2],
        "scope-controller",
        ReviewDecision::Reject
    );

    std::cout << "\nFinal Decisions\n";
    std::cout << "---------------\n";

    for (const auto& review : reviews) {
        std::cout
            << review.request.id
            << ": "
            << toString(review.decision)
            << " by "
            << review.reviewer
            << '\n';
    }

    engine.printAuditLog();
}

void runFailureTests() {
    std::cout << "\nFailure Conditions\n";
    std::cout << "------------------\n";

    ScopeGovernanceEngine engine(createBaseline());

    try {
        ChangeRequest invalidRequest{
            "CR-INVALID",
            "Negative effort",
            "This request intentionally contains invalid effort.",
            "tester",
            {"SCOPE-101"},
            -3.0,
            "Validation test."
        };

        engine.analyze(invalidRequest);
    } catch (const std::exception& error) {
        std::cout
            << "Rejected invalid request: "
            << error.what()
            << '\n';
    }

    try {
        ChangeRequest unmappedRequest{
            "CR-UNMAPPED",
            "Unmapped work",
            "Add an unrelated capability.",
            "tester",
            {},
            4.0,
            "Governance test."
        };

        ScopeReview review = engine.analyze(unmappedRequest);

        // Acceptance is deliberately attempted before the finding is
        // resolved. The engine must reject the governance action.
        engine.finalize(
            review,
            "scope-controller",
            ReviewDecision::Accept
        );
    } catch (const std::exception& error) {
        std::cout
            << "Blocked unsafe acceptance: "
            << error.what()
            << '\n';
    }
}

int main() {
    try {
        std::cout << "SCOPE REVIEW AND SCOPE MANAGEMENT\n";
        std::cout << "=================================\n";

        runCaseStudy();
        runFailureTests();

        std::cout << "\nImplementation Characteristics\n";
        std::cout << "-------------------------------\n";
        std::cout
            << "Scope-item lookup uses unordered_map, giving expected "
            << "constant-time lookup for baseline membership checks.\n";
        std::cout
            << "Finding scans are linear in the number of findings attached "
            << "to one review.\n";
        std::cout
            << "Audit history grows linearly with the number of governance "
            << "events and is retained for traceability.\n";
        std::cout
            << "The engine separates scope analysis from the final human "
            << "governance decision.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }
}
