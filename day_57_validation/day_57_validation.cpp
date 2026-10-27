#include <algorithm>
#include <chrono>
#include <exception>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

enum class ReviewState {
    Commented,
    Approved,
    ChangesRequested,
    Dismissed
};

enum class CheckState {
    Pending,
    Passed,
    Failed
};

enum class ChangeState {
    Draft,
    Open,
    InReview,
    Approved,
    ChangesRequested,
    Merged,
    Closed
};

struct User {
    std::string id;
    std::string name;
    std::string role;
};

struct Commit {
    std::string id;
    std::string message;
    std::string authorId;
    int revision;
};

struct Review {
    std::string reviewerId;
    ReviewState state;
    int revisionReviewed;
    bool dismissed{false};
};

struct StatusCheck {
    std::string name;
    CheckState state;
    bool required;
};

struct BranchProtection {
    int requiredApprovals{2};
    std::set<std::string> requiredChecks;
    bool directPushRestricted{true};
    bool forcePushRestricted{true};
    bool deletionRestricted{true};
    bool requireResolvedConversations{true};
    bool requireLinearHistory{false};
    bool allowAdminBypass{false};
};

struct Branch {
    std::string name;
    bool protectedBranch{false};
    std::vector<std::string> commits;
};

struct PullRequest {
    int number;
    std::string title;
    std::string sourceBranch;
    std::string targetBranch;
    std::string authorId;
    ChangeState state{ChangeState::Open};
    bool draft{false};
    bool mergeConflict{false};
    bool baseSynchronized{true};
    int currentRevision{0};
    int openConversations{0};
    std::vector<Commit> commits;
    std::vector<Review> reviews;
    std::map<std::string, StatusCheck> checks;

    void addCommit(const Commit& commit) {
        if (state == ChangeState::Merged || state == ChangeState::Closed) {
            throw std::logic_error("Completed Pull Requests cannot receive commits.");
        }

        if (commit.authorId != authorId) {
            throw std::invalid_argument("Commit author must match Pull Request author.");
        }

        ++currentRevision;
        commits.push_back(
            Commit{commit.id, commit.message, commit.authorId, currentRevision}
        );

        // Review decisions describe a specific revision. A later revision
        // therefore requires reviewers to reassess their earlier approval.
        state = ChangeState::Open;
    }

    void requestReview() {
        if (draft) {
            throw std::logic_error("Draft Pull Requests cannot enter final review.");
        }

        if (commits.empty()) {
            throw std::logic_error("A Pull Request requires at least one commit.");
        }

        state = ChangeState::InReview;
    }

    void submitReview(const Review& review) {
        if (review.reviewerId == authorId) {
            throw std::invalid_argument("Self-approval is prohibited.");
        }

        reviews.push_back(review);

        if (review.state == ReviewState::ChangesRequested) {
            state = ChangeState::ChangesRequested;
        } else if (review.state == ReviewState::Approved) {
            state = ChangeState::Approved;
        }
    }
};

class GovernanceEngine {
private:
    std::map<std::string, User> users_;

    bool eligibleReviewer(
        const PullRequest& pr,
        const std::string& userId
    ) const {
        auto it = users_.find(userId);

        if (it == users_.end() || userId == pr.authorId) {
            return false;
        }

        return it->second.role == "reviewer" ||
               it->second.role == "project_manager" ||
               it->second.role == "maintainer";
    }

public:
    explicit GovernanceEngine(const std::vector<User>& users) {
        for (const auto& user : users) {
            users_.emplace(user.id, user);
        }
    }

    std::vector<std::string> evaluate(
        const PullRequest& pr,
        const Branch& target,
        const BranchProtection& policy
    ) const {
        std::vector<std::string> failures;

        if (pr.draft) {
            failures.emplace_back("Pull Request is still a draft.");
        }

        if (pr.commits.empty()) {
            failures.emplace_back("No proposed changes exist.");
        }

        if (pr.mergeConflict) {
            failures.emplace_back("Merge conflicts exist.");
        }

        if (!pr.baseSynchronized) {
            failures.emplace_back("Base branch synchronization is required.");
        }

        std::set<std::string> currentApprovers;

        for (const auto& review : pr.reviews) {
            if (review.state == ReviewState::Approved &&
                !review.dismissed &&
                review.revisionReviewed == pr.currentRevision &&
                eligibleReviewer(pr, review.reviewerId)) {
                currentApprovers.insert(review.reviewerId);
            }
        }

        if (static_cast<int>(currentApprovers.size()) <
            policy.requiredApprovals) {
            failures.emplace_back(
                "Required current eligible approvals have not been obtained."
            );
        }

        for (const auto& requiredCheck : policy.requiredChecks) {
            auto it = pr.checks.find(requiredCheck);

            if (it == pr.checks.end()) {
                failures.emplace_back(
                    "Required status check is missing: " + requiredCheck
                );
            } else if (it->second.state != CheckState::Passed) {
                failures.emplace_back(
                    "Required status check has not passed: " + requiredCheck
                );
            }
        }

        if (policy.requireResolvedConversations &&
            pr.openConversations > 0) {
            failures.emplace_back("Unresolved review conversations remain.");
        }

        if (target.protectedBranch && target.name != pr.targetBranch) {
            failures.emplace_back("Target branch does not match protected branch.");
        }

        return failures;
    }

    void merge(
        PullRequest& pr,
        Branch& target,
        const BranchProtection& policy
    ) const {
        auto failures = evaluate(pr, target, policy);

        if (!failures.empty()) {
            throw std::runtime_error(
                "Merge blocked by repository governance."
            );
        }

        for (const auto& commit : pr.commits) {
            target.commits.push_back(commit.id);
        }

        pr.state = ChangeState::Merged;
    }
};

static std::string reviewStateName(ReviewState state) {
    switch (state) {
        case ReviewState::Commented: return "commented";
        case ReviewState::Approved: return "approved";
        case ReviewState::ChangesRequested: return "changes_requested";
        case ReviewState::Dismissed: return "dismissed";
    }
    return "unknown";
}

int main() {
    try {
        const std::vector<User> users{
            {"u1", "Project Manager", "project_manager"},
            {"u2", "Architecture Reviewer", "reviewer"},
            {"u3", "Quality Reviewer", "reviewer"},
            {"u4", "Developer", "developer"}
        };

        GovernanceEngine engine(users);

        Branch mainBranch{
            "main",
            true,
            {"base-001", "base-002"}
        };

        BranchProtection policy;
        policy.requiredApprovals = 2;
        policy.requiredChecks = {
            "scope-validation",
            "security-validation",
            "quality-gate"
        };

        PullRequest pr{
            700,
            "Introduce project risk-control workflow",
            "feature/risk-controls",
            "main",
            "u4"
        };

        pr.addCommit({
            "commit-101",
            "Implement project risk validation",
            "u4",
            0
        });

        pr.requestReview();

        pr.checks["scope-validation"] =
            {"scope-validation", CheckState::Passed, true};
        pr.checks["security-validation"] =
            {"security-validation", CheckState::Passed, true};
        pr.checks["quality-gate"] =
            {"quality-gate", CheckState::Passed, true};

        pr.submitReview({
            "u2",
            ReviewState::Approved,
            pr.currentRevision
        });

        pr.submitReview({
            "u3",
            ReviewState::Approved,
            pr.currentRevision
        });

        std::cout << "Project Change Governance Engine\n";
        std::cout << "================================\n";
        std::cout << "PR #" << pr.number << ": " << pr.title << "\n";

        auto failures = engine.evaluate(pr, mainBranch, policy);

        if (failures.empty()) {
            std::cout << "Merge eligibility: APPROVED\n";
            engine.merge(pr, mainBranch, policy);
            std::cout << "Final state: MERGED\n";
        } else {
            std::cout << "Merge eligibility: BLOCKED\n";
            for (const auto& failure : failures) {
                std::cout << "- " << failure << "\n";
            }
        }

        // A new revision changes the evidence being reviewed.
        PullRequest staleApprovalPr{
            701,
            "Update project cost-control rule",
            "feature/cost-control",
            "main",
            "u4"
        };

        staleApprovalPr.addCommit({
            "commit-201",
            "Add cost threshold rule",
            "u4",
            0
        });

        staleApprovalPr.requestReview();

        staleApprovalPr.checks["scope-validation"] =
            {"scope-validation", CheckState::Passed, true};
        staleApprovalPr.checks["security-validation"] =
            {"security-validation", CheckState::Passed, true};
        staleApprovalPr.checks["quality-gate"] =
            {"quality-gate", CheckState::Passed, true};

        staleApprovalPr.submitReview({
            "u2",
            ReviewState::Approved,
            staleApprovalPr.currentRevision
        });

        staleApprovalPr.submitReview({
            "u3",
            ReviewState::Approved,
            staleApprovalPr.currentRevision
        });

        staleApprovalPr.addCommit({
            "commit-202",
            "Fix cost boundary condition",
            "u4",
            0
        });

        failures = engine.evaluate(
            staleApprovalPr,
            mainBranch,
            policy
        );

        std::cout << "\nStale Approval Scenario\n";
        std::cout << "=======================\n";

        if (failures.empty()) {
            std::cout << "Unexpected result: merge allowed\n";
            return 1;
        }

        std::cout << "Merge eligibility: BLOCKED\n";
        for (const auto& failure : failures) {
            std::cout << "- " << failure << "\n";
        }

        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "Governance failure: " << ex.what() << '\n';
        return 1;
    }
}
