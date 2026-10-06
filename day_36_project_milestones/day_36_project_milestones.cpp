#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Clock = std::chrono::system_clock;
using TimePoint = std::chrono::time_point<Clock>;

std::string timeToString(TimePoint time) {
    std::time_t value = Clock::to_time_t(time);
    std::tm tm_value{};

#ifdef _WIN32
    localtime_s(&tm_value, &value);
#else
    localtime_r(&value, &tm_value);
#endif

    std::ostringstream output;
    output << std::put_time(&tm_value, "%Y-%m-%d %H:%M:%S");
    return output.str();
}

enum class MilestoneStatus {
    Planned,
    Active,
    Completed,
    Blocked,
    Cancelled
};

enum class ReviewState {
    Approved,
    ChangesRequested,
    Commented
};

std::string toString(MilestoneStatus status) {
    switch (status) {
        case MilestoneStatus::Planned: return "planned";
        case MilestoneStatus::Active: return "active";
        case MilestoneStatus::Completed: return "completed";
        case MilestoneStatus::Blocked: return "blocked";
        case MilestoneStatus::Cancelled: return "cancelled";
    }
    return "unknown";
}

std::string toString(ReviewState state) {
    switch (state) {
        case ReviewState::Approved: return "approved";
        case ReviewState::ChangesRequested: return "changes_requested";
        case ReviewState::Commented: return "commented";
    }
    return "unknown";
}

struct ProjectEvent {
    int id;
    std::string type;
    std::string title;
    std::string actor;
    std::string milestoneId;
    TimePoint timestamp;
    std::string details;
};

struct Review {
    std::string reviewer;
    ReviewState state;
    int comments = 0;
    int resolvedComments = 0;

    int unresolvedComments() const {
        return comments - resolvedComments;
    }
};

struct PullRequest {
    int number;
    std::string sourceBranch;
    std::string targetBranch;
    std::string milestoneId;
    std::vector<std::string> commits;
    bool draft = true;
    bool conflicted = false;
    bool merged = false;
    std::vector<Review> reviews;
    std::map<std::string, bool> statusChecks;

    int approvalCount() const {
        std::set<std::string> eligibleApprovers;

        for (const auto& review : reviews) {
            if (
                review.state == ReviewState::Approved &&
                review.unresolvedComments() == 0
            ) {
                eligibleApprovers.insert(review.reviewer);
            }
        }

        return static_cast<int>(eligibleApprovers.size());
    }

    bool hasChangesRequested() const {
        return std::any_of(
            reviews.begin(),
            reviews.end(),
            [](const Review& review) {
                return review.state == ReviewState::ChangesRequested;
            }
        );
    }

    int unresolvedComments() const {
        int total = 0;

        for (const auto& review : reviews) {
            total += review.unresolvedComments();
        }

        return total;
    }
};

struct BranchProtection {
    std::string branch;
    int requiredApprovals = 1;
    std::vector<std::string> requiredStatusChecks;
    bool requireConversationResolution = true;
    bool restrictDirectPushes = true;
    bool allowForcePush = false;
    bool allowDeletion = false;
    bool requireLinearHistory = false;
    bool dismissStaleApprovals = true;
};

struct Milestone {
    std::string id;
    std::string name;
    std::string description;
    int importance;
    MilestoneStatus status = MilestoneStatus::Planned;
    std::set<std::string> dependencies;
};

class RepositoryGovernanceEngine {
private:
    std::string projectId;
    std::string projectName;
    int nextEventId = 1;

    std::map<std::string, Milestone> milestones;
    std::map<int, PullRequest> pullRequests;
    std::map<std::string, BranchProtection> branchPolicies;
    std::vector<ProjectEvent> events;

    Milestone& getMilestone(const std::string& id) {
        auto it = milestones.find(id);

        if (it == milestones.end()) {
            throw std::runtime_error("Unknown milestone: " + id);
        }

        return it->second;
    }

    PullRequest& getPullRequest(int number) {
        auto it = pullRequests.find(number);

        if (it == pullRequests.end()) {
            throw std::runtime_error(
                "Unknown Pull Request: #" + std::to_string(number)
            );
        }

        return it->second;
    }

public:
    RepositoryGovernanceEngine(
        std::string projectId,
        std::string projectName
    )
        : projectId(std::move(projectId)),
          projectName(std::move(projectName)) {}

    void addMilestone(const Milestone& milestone) {
        if (milestone.id.empty()) {
            throw std::invalid_argument("Milestone ID cannot be empty.");
        }

        if (milestone.name.empty()) {
            throw std::invalid_argument("Milestone name cannot be empty.");
        }

        if (milestone.importance < 1 || milestone.importance > 5) {
            throw std::invalid_argument(
                "Milestone importance must be between 1 and 5."
            );
        }

        if (milestones.contains(milestone.id)) {
            throw std::invalid_argument(
                "Duplicate milestone: " + milestone.id
            );
        }

        for (const auto& dependency : milestone.dependencies) {
            if (!milestones.contains(dependency)) {
                throw std::invalid_argument(
                    "Unknown milestone dependency: " + dependency
                );
            }
        }

        milestones.emplace(milestone.id, milestone);
    }

    void recordEvent(
        const std::string& type,
        const std::string& title,
        const std::string& actor,
        const std::string& milestoneId = "",
        const std::string& details = ""
    ) {
        if (!milestoneId.empty() && !milestones.contains(milestoneId)) {
            throw std::invalid_argument(
                "Cannot associate event with unknown milestone."
            );
        }

        events.push_back(ProjectEvent{
            nextEventId++,
            type,
            title,
            actor,
            milestoneId,
            Clock::now(),
            details
        });
    }

    void activateMilestone(const std::string& milestoneId) {
        auto& milestone = getMilestone(milestoneId);

        for (const auto& dependency : milestone.dependencies) {
            if (getMilestone(dependency).status != MilestoneStatus::Completed) {
                throw std::runtime_error(
                    "Cannot activate milestone " + milestoneId +
                    ": dependency " + dependency + " is incomplete."
                );
            }
        }

        if (
            milestone.status != MilestoneStatus::Planned &&
            milestone.status != MilestoneStatus::Blocked
        ) {
            throw std::runtime_error(
                "Invalid activation transition for milestone " + milestoneId
            );
        }

        milestone.status = MilestoneStatus::Active;
    }

    void blockMilestone(
        const std::string& milestoneId,
        const std::string& actor,
        const std::string& reason
    ) {
        auto& milestone = getMilestone(milestoneId);

        if (milestone.status == MilestoneStatus::Completed) {
            throw std::runtime_error(
                "A completed milestone cannot be blocked."
            );
        }

        milestone.status = MilestoneStatus::Blocked;

        recordEvent(
            "milestone_blocked",
            "Milestone blocked: " + milestone.name,
            actor,
            milestoneId,
            reason
        );
    }

    void completeMilestone(
        const std::string& milestoneId,
        const std::string& actor,
        const std::string& reason
    ) {
        auto& milestone = getMilestone(milestoneId);

        for (const auto& [number, pr] : pullRequests) {
            if (
                pr.milestoneId == milestoneId &&
                !pr.merged
            ) {
                throw std::runtime_error(
                    "Milestone cannot be completed because Pull Request #" +
                    std::to_string(number) + " is not merged."
                );
            }
        }

        if (milestone.status == MilestoneStatus::Cancelled) {
            throw std::runtime_error(
                "A cancelled milestone cannot be completed."
            );
        }

        milestone.status = MilestoneStatus::Completed;

        recordEvent(
            "milestone_completed",
            "Milestone completed: " + milestone.name,
            actor,
            milestoneId,
            reason
        );
    }

    void configureBranchProtection(const BranchProtection& policy) {
        if (policy.requiredApprovals < 0) {
            throw std::invalid_argument(
                "Required approvals cannot be negative."
            );
        }

        branchPolicies[policy.branch] = policy;
    }

    void createPullRequest(
        int number,
        const std::string& sourceBranch,
        const std::string& targetBranch,
        const std::string& milestoneId,
        std::vector<std::string> commits,
        const std::string& actor
    ) {
        if (pullRequests.contains(number)) {
            throw std::invalid_argument(
                "Pull Request already exists: #" + std::to_string(number)
            );
        }

        if (!milestones.contains(milestoneId)) {
            throw std::invalid_argument("Unknown milestone.");
        }

        if (sourceBranch == targetBranch) {
            throw std::invalid_argument(
                "Source and target branches must differ."
            );
        }

        if (commits.empty()) {
            throw std::invalid_argument(
                "Pull Request requires at least one commit."
            );
        }

        PullRequest pr{
            number,
            sourceBranch,
            targetBranch,
            milestoneId,
            std::move(commits)
        };

        pullRequests.emplace(number, std::move(pr));

        recordEvent(
            "pull_request_opened",
            "Pull Request #" + std::to_string(number) + " opened",
            actor,
            milestoneId,
            sourceBranch + " -> " + targetBranch
        );
    }

    void markReadyForReview(int number, const std::string& actor) {
        auto& pr = getPullRequest(number);

        if (pr.merged) {
            throw std::runtime_error(
                "Merged Pull Request cannot become ready for review."
            );
        }

        pr.draft = false;

        recordEvent(
            "pull_request_ready",
            "Pull Request #" + std::to_string(number) +
                " marked ready for review",
            actor,
            pr.milestoneId
        );
    }

    void submitReview(
        int number,
        const Review& review
    ) {
        auto& pr = getPullRequest(number);

        if (review.comments < 0 ||
            review.resolvedComments < 0 ||
            review.resolvedComments > review.comments) {
            throw std::invalid_argument(
                "Invalid review comment counts."
            );
        }

        pr.reviews.push_back(review);

        recordEvent(
            review.state == ReviewState::Approved
                ? "approval_granted"
                : "code_review_completed",
            "Review submitted for Pull Request #" +
                std::to_string(number),
            review.reviewer,
            pr.milestoneId,
            toString(review.state)
        );
    }

    void setStatusCheck(
        int number,
        const std::string& check,
        bool passed,
        const std::string& actor
    ) {
        auto& pr = getPullRequest(number);

        pr.statusChecks[check] = passed;

        recordEvent(
            "status_check",
            check + (passed ? " passed" : " failed"),
            actor,
            pr.milestoneId
        );
    }

    std::pair<bool, std::vector<std::string>>
    evaluateMergeEligibility(int number) {
        auto& pr = getPullRequest(number);
        std::vector<std::string> failures;

        auto policyIt = branchPolicies.find(pr.targetBranch);

        if (policyIt == branchPolicies.end()) {
            failures.push_back(
                "No branch protection policy is configured for the target branch."
            );
        }

        if (pr.draft) {
            failures.push_back("Pull Request is still a draft.");
        }

        if (pr.conflicted) {
            failures.push_back("Pull Request has merge conflicts.");
        }

        if (pr.hasChangesRequested()) {
            failures.push_back("A reviewer has requested changes.");
        }

        if (policyIt != branchPolicies.end()) {
            const auto& policy = policyIt->second;

            if (pr.approvalCount() < policy.requiredApprovals) {
                failures.push_back(
                    "Required approvals: " +
                    std::to_string(policy.requiredApprovals) +
                    ", actual approvals: " +
                    std::to_string(pr.approvalCount()) +
                    "."
                );
            }

            for (const auto& check : policy.requiredStatusChecks) {
                auto checkIt = pr.statusChecks.find(check);

                if (
                    checkIt == pr.statusChecks.end() ||
                    !checkIt->second
                ) {
                    failures.push_back(
                        "Required status check is missing or failed: " +
                        check
                    );
                }
            }

            if (
                policy.requireConversationResolution &&
                pr.unresolvedComments() > 0
            ) {
                failures.push_back(
                    "Review conversations contain unresolved comments."
                );
            }
        }

        return {failures.empty(), failures};
    }

    void mergePullRequest(
        int number,
        const std::string& actor
    ) {
        auto& pr = getPullRequest(number);

        auto [eligible, failures] =
            evaluateMergeEligibility(number);

        if (!eligible) {
            std::ostringstream message;
            message << "Pull Request #" << number
                    << " cannot be merged:";

            for (const auto& failure : failures) {
                message << "\n - " << failure;
            }

            throw std::runtime_error(message.str());
        }

        pr.merged = true;

        recordEvent(
            "merged",
            "Pull Request #" + std::to_string(number) +
                " merged into " + pr.targetBranch,
            actor,
            pr.milestoneId
        );
    }

    void synchronizePullRequest(
        int number,
        const std::string& newCommit,
        const std::string& actor
    ) {
        auto& pr = getPullRequest(number);

        if (pr.merged) {
            throw std::runtime_error(
                "Merged Pull Request cannot be synchronized."
            );
        }

        if (newCommit.empty()) {
            throw std::invalid_argument(
                "Synchronization requires a commit."
            );
        }

        pr.commits.push_back(newCommit);

        auto policyIt = branchPolicies.find(pr.targetBranch);

        if (
            policyIt != branchPolicies.end() &&
            policyIt->second.dismissStaleApprovals
        ) {
            for (auto& review : pr.reviews) {
                if (review.state == ReviewState::Approved) {
                    review.state = ReviewState::Commented;
                }
            }
        }

        recordEvent(
            "pull_request_synchronized",
            "Pull Request #" + std::to_string(number) +
                " synchronized with new changes",
            actor,
            pr.milestoneId,
            newCommit
        );
    }

    std::vector<ProjectEvent> importantEvents(
        const std::optional<std::string>& milestoneFilter = std::nullopt
    ) const {
        const std::set<std::string> importantTypes{
            "project_started",
            "requirement_approved",
            "design_completed",
            "pull_request_opened",
            "approval_granted",
            "status_check",
            "merged",
            "released",
            "milestone_completed",
            "milestone_blocked"
        };

        std::vector<ProjectEvent> result;

        for (const auto& event : events) {
            if (!importantTypes.contains(event.type)) {
                continue;
            }

            if (
                milestoneFilter &&
                event.milestoneId != *milestoneFilter
            ) {
                continue;
            }

            result.push_back(event);
        }

        return result;
    }

    void printMilestoneReport(
        const std::string& milestoneId
    ) const {
        const auto& milestone = milestones.at(milestoneId);

        int prCount = 0;
        int mergedCount = 0;
        int eventCount = 0;

        for (const auto& [number, pr] : pullRequests) {
            if (pr.milestoneId == milestoneId) {
                ++prCount;
                if (pr.merged) {
                    ++mergedCount;
                }
            }
        }

        for (const auto& event : events) {
            if (event.milestoneId == milestoneId) {
                ++eventCount;
            }
        }

        std::cout
            << "\nMilestone: " << milestone.name
            << "\nStatus: " << toString(milestone.status)
            << "\nImportance: " << milestone.importance
            << "\nPull Requests: " << prCount
            << "\nMerged Pull Requests: " << mergedCount
            << "\nImportant events recorded: " << eventCount
            << "\n";
    }

    void printTimeline() const {
        std::cout << "\nPROJECT EVENT TIMELINE\n";
        std::cout << "============================================================\n";

        for (const auto& event : events) {
            std::cout
                << timeToString(event.timestamp)
                << " | "
                << event.type
                << " | "
                << event.actor
                << " | "
                << event.title;

            if (!event.milestoneId.empty()) {
                std::cout << " | milestone=" << event.milestoneId;
            }

            if (!event.details.empty()) {
                std::cout << " | " << event.details;
            }

            std::cout << "\n";
        }
    }
};

int main() {
    try {
        RepositoryGovernanceEngine engine(
            "PRJ-904",
            "Enterprise Billing Modernization"
        );

        engine.addMilestone({
            "M-REQ",
            "Billing Requirements Approved",
            "Formal approval of billing-service requirements.",
            5
        });

        engine.addMilestone({
            "M-CORE",
            "Billing Core Implementation",
            "Implement and validate billing calculation services.",
            5,
            MilestoneStatus::Planned,
            {"M-REQ"}
        });

        engine.addMilestone({
            "M-REL",
            "Production Billing Release",
            "Release reviewed and approved billing implementation.",
            5,
            MilestoneStatus::Planned,
            {"M-CORE"}
        });

        engine.recordEvent(
            "project_started",
            "Billing modernization project started",
            "program-manager",
            "M-REQ"
        );

        engine.activateMilestone("M-REQ");

        engine.recordEvent(
            "requirement_approved",
            "Billing requirements baseline approved",
            "product-owner",
            "M-REQ"
        );

        engine.completeMilestone(
            "M-REQ",
            "product-owner",
            "Requirements signed off."
        );

        engine.activateMilestone("M-CORE");

        engine.recordEvent(
            "design_completed",
            "Billing architecture completed",
            "solution-architect",
            "M-CORE"
        );

        engine.configureBranchProtection({
            "main",
            2,
            {
                "unit-tests",
                "integration-tests",
                "security-scan"
            },
            true,
            true,
            false,
            false,
            true,
            true
        });

        engine.createPullRequest(
            812,
            "feature/billing-core",
            "main",
            "M-CORE",
            {
                "Implement invoice calculation",
                "Add tax calculation",
                "Add reconciliation validation"
            },
            "developer"
        );

        engine.markReadyForReview(812, "developer");

        engine.submitReview(
            812,
            {
                "senior-engineer",
                ReviewState::Approved,
                2,
                2
            }
        );

        engine.submitReview(
            812,
            {
                "security-reviewer",
                ReviewState::Commented,
                1,
                0
            }
        );

        auto initialCheck =
            engine.evaluateMergeEligibility(812);

        std::cout << "\nINITIAL MERGE EVALUATION\n";

        if (!initialCheck.first) {
            for (const auto& reason : initialCheck.second) {
                std::cout << " - " << reason << "\n";
            }
        }

        engine.submitReview(
            812,
            {
                "security-reviewer",
                ReviewState::Approved,
                1,
                1
            }
        );

        engine.setStatusCheck(
            812,
            "unit-tests",
            true,
            "ci"
        );

        engine.setStatusCheck(
            812,
            "integration-tests",
            true,
            "ci"
        );

        engine.setStatusCheck(
            812,
            "security-scan",
            true,
            "security-ci"
        );

        auto finalCheck =
            engine.evaluateMergeEligibility(812);

        std::cout << "\nFINAL MERGE EVALUATION\n";
        std::cout
            << "Eligible: "
            << std::boolalpha
            << finalCheck.first
            << "\n";

        if (!finalCheck.first) {
            for (const auto& reason : finalCheck.second) {
                std::cout << " - " << reason << "\n";
            }
        }

        engine.mergePullRequest(
            812,
            "release-manager"
        );

        engine.completeMilestone(
            "M-CORE",
            "engineering-manager",
            "Implementation merged after protected-branch governance checks."
        );

        engine.activateMilestone("M-REL");

        engine.recordEvent(
            "released",
            "Billing service version 4.0 deployed",
            "release-manager",
            "M-REL",
            "Production smoke tests passed."
        );

        engine.completeMilestone(
            "M-REL",
            "release-manager",
            "Production release validated."
        );

        engine.printMilestoneReport("M-REQ");
        engine.printMilestoneReport("M-CORE");
        engine.printMilestoneReport("M-REL");

        engine.printTimeline();

        std::cout << "\nIMPORTANT PROJECT EVENTS\n";

        for (const auto& event : engine.importantEvents()) {
            std::cout
                << event.type
                << " | "
                << event.title
                << " | actor="
                << event.actor
                << "\n";
        }
    }
    catch (const std::exception& error) {
        std::cerr
            << "Governance error: "
            << error.what()
            << "\n";

        return 1;
    }

    return 0;
}
