#include <algorithm>
#include <iostream>
#include <map>
#include <set>
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
    std::string author;
};

struct Review {
    std::string reviewer;
    ReviewState state;
    std::string commitSha;
    bool dismissed = false;
    std::vector<std::string> comments;
};

struct StatusCheck {
    std::string name;
    bool passed;
    std::string commitSha;
};

struct BranchProtection {
    std::size_t requiredReviews = 2;
    std::set<std::string> requiredChecks{"tests", "security"};
    bool requireConversationResolution = true;
    bool allowDirectPush = false;
    bool allowForcePush = false;
    bool allowDeletion = false;
    bool requireLinearHistory = true;
    bool allowAdminBypass = false;
};

struct MergeDecision {
    bool eligible;
    std::vector<std::string> failures;
};

class PullRequest {
private:
    int number_;
    std::string title_;
    std::string sourceBranch_;
    std::string targetBranch_;
    std::string author_;
    PullRequestState state_ = PullRequestState::Draft;

    std::vector<Commit> commits_;
    std::set<std::string> requestedReviewers_;
    std::vector<Review> reviews_;
    std::map<std::string, StatusCheck> checks_;
    std::size_t unresolvedConversations_ = 0;
    std::string headSha_;

public:
    PullRequest(
        int number,
        std::string title,
        std::string sourceBranch,
        std::string targetBranch,
        std::string author,
        bool draft
    )
        : number_(number),
          title_(std::move(title)),
          sourceBranch_(std::move(sourceBranch)),
          targetBranch_(std::move(targetBranch)),
          author_(std::move(author)),
          state_(draft ? PullRequestState::Draft : PullRequestState::Open) {

        if (title_.empty()) {
            throw std::invalid_argument("Pull Request title is required.");
        }

        if (sourceBranch_ == targetBranch_) {
            throw std::invalid_argument(
                "Source and target branches must differ."
            );
        }
    }

    int number() const {
        return number_;
    }

    const std::string& headSha() const {
        return headSha_;
    }

    PullRequestState state() const {
        return state_;
    }

    const std::vector<Review>& reviews() const {
        return reviews_;
    }

    const std::vector<Commit>& commits() const {
        return commits_;
    }

    const std::map<std::string, StatusCheck>& checks() const {
        return checks_;
    }

    std::size_t unresolvedConversations() const {
        return unresolvedConversations_;
    }

    const std::string& author() const {
        return author_;
    }

    void open() {
        if (state_ != PullRequestState::Draft &&
            state_ != PullRequestState::Closed) {
            throw std::logic_error("Pull Request cannot be opened.");
        }
        state_ = PullRequestState::Open;
    }

    void close() {
        if (state_ == PullRequestState::Merged) {
            throw std::logic_error("Merged Pull Request cannot be closed.");
        }
        state_ = PullRequestState::Closed;
    }

    void reopen() {
        if (state_ != PullRequestState::Closed) {
            throw std::logic_error("Only closed Pull Requests can be reopened.");
        }
        state_ = PullRequestState::Open;
    }

    void addCommit(Commit commit) {
        if (state_ == PullRequestState::Merged) {
            throw std::logic_error("Cannot modify a merged Pull Request.");
        }

        if (commit.sha.empty() || commit.author.empty()) {
            throw std::invalid_argument(
                "Commit SHA and author are required."
            );
        }

        auto duplicate = std::find_if(
            commits_.begin(),
            commits_.end(),
            [&](const Commit& existing) {
                return existing.sha == commit.sha;
            }
        );

        if (duplicate != commits_.end()) {
            throw std::invalid_argument("Duplicate commit SHA.");
        }

        commits_.push_back(std::move(commit));
        headSha_ = commits_.back().sha;

        // A review is tied to the revision that was inspected.
        // New commits therefore make old approvals stale.
        for (auto& review : reviews_) {
            if (review.commitSha != headSha_ &&
                review.state == ReviewState::Approved) {
                review.dismissed = true;
            }
        }
    }

    void requestReview(const std::string& reviewer) {
        if (reviewer.empty() || reviewer == author_) {
            throw std::invalid_argument(
                "Author cannot be a required reviewer."
            );
        }
        requestedReviewers_.insert(reviewer);
    }

    void submitReview(
        const std::string& reviewer,
        ReviewState state,
        std::vector<std::string> comments = {}
    ) {
        if (state_ != PullRequestState::Open) {
            throw std::logic_error(
                "Reviews require an open Pull Request."
            );
        }

        if (reviewer.empty() || reviewer == author_) {
            throw std::invalid_argument(
                "Self-review is not permitted."
            );
        }

        reviews_.push_back(
            Review{
                reviewer,
                state,
                headSha_,
                false,
                std::move(comments)
            }
        );
    }

    void setStatusCheck(const std::string& name, bool passed) {
        if (headSha_.empty()) {
            throw std::logic_error(
                "A status check requires a current revision."
            );
        }

        checks_[name] = StatusCheck{name, passed, headSha_};
    }

    void addConversation() {
        ++unresolvedConversations_;
    }

    void resolveConversation() {
        if (unresolvedConversations_ == 0) {
            throw std::logic_error(
                "No unresolved conversation exists."
            );
        }
        --unresolvedConversations_;
    }

    void synchronizeBase(const std::string& newHeadSha) {
        if (state_ != PullRequestState::Open) {
            throw std::logic_error(
                "Only open Pull Requests can be synchronized."
            );
        }

        headSha_ = newHeadSha;

        // Base-branch synchronization changes the revision under review.
        for (auto& review : reviews_) {
            if (review.state == ReviewState::Approved) {
                review.dismissed = true;
            }
        }

        for (auto& [name, check] : checks_) {
            check.passed = false;
        }
    }

    void markMerged() {
        if (state_ != PullRequestState::Open) {
            throw std::logic_error(
                "Only open Pull Requests can be merged."
            );
        }
        state_ = PullRequestState::Merged;
    }
};

class GovernanceEngine {
private:
    BranchProtection policy_;

public:
    explicit GovernanceEngine(BranchProtection policy)
        : policy_(std::move(policy)) {}

    MergeDecision evaluate(const PullRequest& pr) const {
        std::vector<std::string> failures;

        if (pr.state() != PullRequestState::Open) {
            failures.push_back("Pull Request must be open.");
        }

        if (pr.commits().empty()) {
            failures.push_back("Pull Request contains no commits.");
        }

        std::set<std::string> eligibleApprovers;

        for (const auto& review : pr.reviews()) {
            if (
                review.state == ReviewState::Approved &&
                !review.dismissed &&
                review.commitSha == pr.headSha() &&
                review.reviewer != pr.author()
            ) {
                eligibleApprovers.insert(review.reviewer);
            }
        }

        if (eligibleApprovers.size() < policy_.requiredReviews) {
            failures.push_back(
                "Required current approval count has not been reached."
            );
        }

        for (const auto& review : pr.reviews()) {
            if (
                review.state == ReviewState::ChangesRequested &&
                !review.dismissed &&
                review.commitSha == pr.headSha()
            ) {
                failures.push_back(
                    "An active changes-requested review remains."
                );
                break;
            }
        }

        for (const auto& required : policy_.requiredChecks) {
            auto it = pr.checks().find(required);

            if (
                it == pr.checks().end() ||
                !it->second.passed ||
                it->second.commitSha != pr.headSha()
            ) {
                failures.push_back(
                    "Required status check '" + required +
                    "' has not passed for the current revision."
                );
            }
        }

        if (
            policy_.requireConversationResolution &&
            pr.unresolvedConversations() > 0
        ) {
            failures.push_back(
                "Unresolved review conversations remain."
            );
        }

        return MergeDecision{failures.empty(), failures};
    }

    void merge(PullRequest& pr, MergeStrategy strategy) const {
        MergeDecision decision = evaluate(pr);

        if (!decision.eligible) {
            std::string message = "Merge blocked:";
            for (const auto& failure : decision.failures) {
                message += " " + failure;
            }
            throw std::runtime_error(message);
        }

        pr.markMerged();

        const char* strategyName =
            strategy == MergeStrategy::Squash ? "squash" :
            strategy == MergeStrategy::Rebase ? "rebase" :
            "merge commit";

        std::cout << "Pull Request #" << pr.number()
                  << " merged using " << strategyName
                  << " strategy.\n";
    }
};

int main() {
    try {
        BranchProtection protection;
        protection.requiredReviews = 2;
        protection.requiredChecks = {"tests", "security"};
        protection.requireConversationResolution = true;
        protection.requireLinearHistory = true;
        protection.allowDirectPush = false;
        protection.allowForcePush = false;
        protection.allowDeletion = false;

        GovernanceEngine governance(protection);

        PullRequest pr(
            42,
            "Harden payment authorization",
            "feature/payment-policy",
            "main",
            "alice",
            true
        );

        pr.addCommit({
            "a100",
            "Add authorization policy",
            "alice"
        });

        pr.requestReview("bob");
        pr.requestReview("carol");
        pr.open();

        pr.submitReview(
            "bob",
            ReviewState::Approved,
            {"Authorization boundaries are correct."}
        );

        pr.submitReview(
            "carol",
            ReviewState::ChangesRequested,
            {"Add a regression test for expired credentials."}
        );

        pr.addConversation();
        pr.setStatusCheck("tests", true);
        pr.setStatusCheck("security", true);

        MergeDecision initial = governance.evaluate(pr);

        std::cout << "Initial merge eligibility: "
                  << (initial.eligible ? "eligible" : "blocked")
                  << "\n";

        for (const auto& failure : initial.failures) {
            std::cout << " - " << failure << "\n";
        }

        // A new commit creates a new revision and invalidates the old approval.
        pr.addCommit({
            "a101",
            "Add expired credential regression coverage",
            "alice"
        });

        pr.submitReview(
            "bob",
            ReviewState::Approved,
            {"Regression coverage is present."}
        );

        pr.submitReview(
            "carol",
            ReviewState::Approved,
            {"Requested change has been addressed."}
        );

        pr.resolveConversation();
        pr.setStatusCheck("tests", true);
        pr.setStatusCheck("security", true);

        MergeDecision finalDecision = governance.evaluate(pr);

        std::cout << "\nFinal merge eligibility: "
                  << (finalDecision.eligible ? "eligible" : "blocked")
                  << "\n";

        if (finalDecision.eligible) {
            governance.merge(pr, MergeStrategy::Squash);
        }

        std::cout << "Governance simulation completed.\n";
    }
    catch (const std::exception& error) {
        std::cerr << "Governance error: "
                  << error.what() << "\n";
        return 1;
    }

    return 0;
}
