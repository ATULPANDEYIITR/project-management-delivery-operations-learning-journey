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

enum class PullRequestState {
    Draft,
    Open,
    Closed,
    Merged
};

enum class ReviewState {
    Commented,
    Approved,
    ChangesRequested,
    Dismissed
};

enum class MergeStrategy {
    MergeCommit,
    Squash,
    Rebase
};

struct Commit {
    std::string sha;
    std::string message;
    int changedFiles{};
    int additions{};
    int deletions{};
};

struct Review {
    std::string reviewer;
    ReviewState state;
    int revision{};
    int inlineComments{};
};

struct StatusCheck {
    std::string name;
    bool passed{};
    int revision{};
};

struct BranchProtection {
    int requiredApprovals{};
    std::set<std::string> requiredChecks;
    bool dismissStaleApprovals{true};
    bool requireConversationResolution{true};
    bool restrictDirectPush{true};
    bool allowForcePush{false};
    bool allowDeletion{false};
    bool requireLinearHistory{false};
    std::set<MergeStrategy> allowedStrategies;
};

class PullRequest {
private:
    int number_;
    std::string sourceBranch_;
    std::string targetBranch_;
    std::string title_;
    PullRequestState state_{PullRequestState::Open};
    int revision_{1};
    bool synchronized_{true};
    bool conflicts_{false};
    int unresolvedConversations_{0};

    std::vector<Commit> commits_;
    std::vector<Review> reviews_;
    std::map<std::string, StatusCheck> statusChecks_;

public:
    PullRequest(
        int number,
        std::string sourceBranch,
        std::string targetBranch,
        std::string title
    )
        : number_(number),
          sourceBranch_(std::move(sourceBranch)),
          targetBranch_(std::move(targetBranch)),
          title_(std::move(title)) {

        if (number_ <= 0) {
            throw std::invalid_argument("PR number must be positive.");
        }

        if (sourceBranch_.empty() ||
            targetBranch_.empty() ||
            sourceBranch_ == targetBranch_) {
            throw std::invalid_argument(
                "Source and target branches must be different."
            );
        }

        if (title_.size() < 5) {
            throw std::invalid_argument("PR title is too short.");
        }
    }

    void addCommit(const Commit& commit) {
        if (state_ != PullRequestState::Draft &&
            state_ != PullRequestState::Open) {
            throw std::logic_error(
                "Commits cannot be added after closure or merge."
            );
        }

        if (commit.sha.size() < 7) {
            throw std::invalid_argument(
                "Commit SHA must contain at least seven characters."
            );
        }

        if (commit.changedFiles < 0 ||
            commit.additions < 0 ||
            commit.deletions < 0) {
            throw std::invalid_argument(
                "Commit metrics cannot be negative."
            );
        }

        commits_.push_back(commit);
        ++revision_;
        synchronized_ = true;
    }

    void submitReview(const Review& review) {
        if (state_ != PullRequestState::Open) {
            throw std::logic_error("Only open PRs accept reviews.");
        }

        if (review.reviewer.empty()) {
            throw std::invalid_argument("Reviewer cannot be empty.");
        }

        reviews_.push_back(review);
    }

    void setStatusCheck(const StatusCheck& check) {
        if (check.name.empty()) {
            throw std::invalid_argument("Status check name is required.");
        }

        statusChecks_[check.name] = check;
    }

    void updateBaseBranch(bool conflicts) {
        if (state_ != PullRequestState::Open) {
            throw std::logic_error(
                "Only open PRs can be affected by base updates."
            );
        }

        ++revision_;
        synchronized_ = false;
        conflicts_ = conflicts;
    }

    void synchronize() {
        if (state_ != PullRequestState::Open) {
            throw std::logic_error("Only open PRs can synchronize.");
        }

        synchronized_ = true;
        conflicts_ = false;
    }

    void setUnresolvedConversations(int count) {
        if (count < 0) {
            throw std::invalid_argument(
                "Unresolved conversation count cannot be negative."
            );
        }

        unresolvedConversations_ = count;
    }

    void close() {
        if (state_ == PullRequestState::Merged) {
            throw std::logic_error("A merged PR cannot be closed.");
        }

        state_ = PullRequestState::Closed;
    }

    void reopen() {
        if (state_ != PullRequestState::Closed) {
            throw std::logic_error("Only a closed PR can be reopened.");
        }

        state_ = PullRequestState::Open;
    }

    void markMerged() {
        state_ = PullRequestState::Merged;
    }

    PullRequestState state() const {
        return state_;
    }

    int revision() const {
        return revision_;
    }

    int changedFiles() const {
        int total = 0;

        for (const auto& commit : commits_) {
            total += commit.changedFiles;
        }

        return total;
    }

    int estimatedReviewMinutes() const {
        // A simple capacity model: four minutes per changed file,
        // with a ten-minute floor for small but non-trivial changes.
        return std::max(10, changedFiles() * 4);
    }

    const std::vector<Review>& reviews() const {
        return reviews_;
    }

    const std::map<std::string, StatusCheck>& statusChecks() const {
        return statusChecks_;
    }

    bool synchronized() const {
        return synchronized_;
    }

    bool conflicts() const {
        return conflicts_;
    }

    int unresolvedConversations() const {
        return unresolvedConversations_;
    }

    bool hasCommits() const {
        return !commits_.empty();
    }
};

struct MergeEvaluation {
    bool eligible{true};
    std::vector<std::string> reasons;

    void block(const std::string& reason) {
        eligible = false;
        reasons.push_back(reason);
    }
};

class MergeEligibilityEngine {
private:
    BranchProtection policy_;

public:
    explicit MergeEligibilityEngine(BranchProtection policy)
        : policy_(std::move(policy)) {}

    MergeEvaluation evaluate(
        const PullRequest& pr,
        const std::set<std::string>& eligibleReviewers,
        MergeStrategy strategy
    ) const {
        MergeEvaluation result;

        if (pr.state() != PullRequestState::Open) {
            result.block("Pull Request is not open.");
        }

        if (!pr.hasCommits()) {
            result.block("Pull Request contains no commits.");
        }

        if (!pr.synchronized()) {
            result.block("Pull Request is not synchronized with the base branch.");
        }

        if (pr.conflicts()) {
            result.block("Merge conflicts remain unresolved.");
        }

        if (!policy_.allowedStrategies.contains(strategy)) {
            result.block("Selected merge strategy is not allowed.");
        }

        std::map<std::string, Review> latestReviews;

        for (const auto& review : pr.reviews()) {
            latestReviews[review.reviewer] = review;
        }

        int approvals = 0;
        bool changesRequested = false;

        for (const auto& [reviewer, review] : latestReviews) {
            if (!eligibleReviewers.contains(reviewer)) {
                continue;
            }

            if (review.state == ReviewState::ChangesRequested) {
                changesRequested = true;
            }

            const bool currentRevision =
                review.revision == pr.revision();

            if (review.state == ReviewState::Approved &&
                (!policy_.dismissStaleApprovals || currentRevision)) {
                ++approvals;
            }
        }

        if (changesRequested) {
            result.block(
                "An eligible reviewer currently requests changes."
            );
        }

        if (approvals < policy_.requiredApprovals) {
            std::ostringstream message;
            message << "Required approvals: "
                    << policy_.requiredApprovals
                    << ", eligible approvals: "
                    << approvals
                    << ".";
            result.block(message.str());
        }

        for (const auto& checkName : policy_.requiredChecks) {
            auto it = pr.statusChecks().find(checkName);

            if (it == pr.statusChecks().end()) {
                result.block(
                    "Required status check '" + checkName + "' is missing."
                );
                continue;
            }

            if (!it->second.passed) {
                result.block(
                    "Required status check '" + checkName + "' failed."
                );
            }

            if (policy_.dismissStaleApprovals &&
                it->second.revision != pr.revision()) {
                result.block(
                    "Required status check '" + checkName +
                    "' is stale."
                );
            }
        }

        if (policy_.requireConversationResolution &&
            pr.unresolvedConversations() > 0) {
            result.block(
                "Unresolved review conversations remain."
            );
        }

        return result;
    }
};

std::string strategyName(MergeStrategy strategy) {
    switch (strategy) {
        case MergeStrategy::MergeCommit:
            return "merge commit";
        case MergeStrategy::Squash:
            return "squash";
        case MergeStrategy::Rebase:
            return "rebase";
    }

    return "unknown";
}

int main() {
    try {
        BranchProtection protection{
            .requiredApprovals = 2,
            .requiredChecks = {"unit-tests", "security-scan"},
            .dismissStaleApprovals = true,
            .requireConversationResolution = true,
            .restrictDirectPush = true,
            .allowForcePush = false,
            .allowDeletion = false,
            .requireLinearHistory = true,
            .allowedStrategies = {MergeStrategy::Squash}
        };

        PullRequest pr(
            501,
            "feature/resource-cost-review",
            "main",
            "Evaluate repository cost and engineering resources"
        );

        pr.addCommit({
            "1234567abcdef",
            "Add resource accounting model",
            7,
            220,
            30
        });

        pr.addCommit({
            "7654321fedcba",
            "Add governance merge rules",
            5,
            140,
            15
        });

        // The revision is captured explicitly. This allows the engine to
        // distinguish current approvals from approvals made before a
        // subsequent source/base change.
        const int reviewRevision = pr.revision();

        pr.submitReview({
            "alice",
            ReviewState::Approved,
            reviewRevision,
            2
        });

        pr.submitReview({
            "bob",
            ReviewState::ChangesRequested,
            reviewRevision,
            3
        });

        pr.setStatusCheck({
            "unit-tests",
            true,
            pr.revision()
        });

        pr.setStatusCheck({
            "security-scan",
            true,
            pr.revision()
        });

        pr.setUnresolvedConversations(1);

        MergeEligibilityEngine engine(protection);

        const std::set<std::string> eligibleReviewers{
            "alice", "bob", "carol"
        };

        auto evaluation = engine.evaluate(
            pr,
            eligibleReviewers,
            MergeStrategy::Squash
        );

        std::cout << "PR #" << 501 << '\n';
        std::cout << "Changed files: "
                  << pr.changedFiles() << '\n';
        std::cout << "Estimated review effort: "
                  << pr.estimatedReviewMinutes()
                  << " minutes\n";
        std::cout << "Initial merge eligibility: "
                  << std::boolalpha
                  << evaluation.eligible
                  << "\n\n";

        for (const auto& reason : evaluation.reasons) {
            std::cout << "BLOCKED: " << reason << '\n';
        }

        // Bob updates the review after resolving the issue.
        pr.submitReview({
            "bob",
            ReviewState::Approved,
            pr.revision(),
            1
        });

        pr.setUnresolvedConversations(0);

        evaluation = engine.evaluate(
            pr,
            eligibleReviewers,
            MergeStrategy::Squash
        );

        std::cout << "\nAfter review correction:\n";
        std::cout << "Merge eligibility: "
                  << evaluation.eligible
                  << '\n';

        if (evaluation.eligible) {
            pr.markMerged();
            std::cout << "Merged using "
                      << strategyName(MergeStrategy::Squash)
                      << " strategy.\n";
        } else {
            for (const auto& reason : evaluation.reasons) {
                std::cout << "BLOCKED: " << reason << '\n';
            }
        }

        // The following state transition demonstrates a base update.
        // A real repository would re-run policy checks before merge.
        std::cout << "\nRepository governance state: merged PR is immutable.\n";
    }
    catch (const std::exception& error) {
        std::cerr << "Governance engine error: "
                  << error.what()
                  << '\n';
        return 1;
    }

    return 0;
}
