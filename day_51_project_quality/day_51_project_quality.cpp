#include <algorithm>
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

enum class CheckState {
    Pending,
    Passed,
    Failed
};

enum class MergeStrategy {
    MergeCommit,
    Squash,
    Rebase
};

std::string toString(PullRequestState state) {
    switch (state) {
        case PullRequestState::Draft: return "draft";
        case PullRequestState::Open: return "open";
        case PullRequestState::Closed: return "closed";
        case PullRequestState::Merged: return "merged";
    }
    return "unknown";
}

std::string toString(ReviewState state) {
    switch (state) {
        case ReviewState::Commented: return "commented";
        case ReviewState::Approved: return "approved";
        case ReviewState::ChangesRequested: return "changes_requested";
        case ReviewState::Dismissed: return "dismissed";
    }
    return "unknown";
}

std::string toString(CheckState state) {
    switch (state) {
        case CheckState::Pending: return "pending";
        case CheckState::Passed: return "passed";
        case CheckState::Failed: return "failed";
    }
    return "unknown";
}

std::string toString(MergeStrategy strategy) {
    switch (strategy) {
        case MergeStrategy::MergeCommit: return "merge_commit";
        case MergeStrategy::Squash: return "squash";
        case MergeStrategy::Rebase: return "rebase";
    }
    return "unknown";
}

struct Commit {
    std::string sha;
    std::string message;
    std::string author;
};

struct Review {
    std::string reviewer;
    ReviewState state;
    std::string commitSha;
};

struct StatusCheck {
    std::string name;
    CheckState state;
    std::string commitSha;
};

struct BranchProtection {
    std::string branch;
    std::size_t requiredReviews = 1;
    std::set<std::string> requiredChecks;
    bool dismissStaleReviews = true;
    bool requireConversationResolution = true;
    bool restrictDirectPush = true;
    bool allowForcePush = false;
    bool allowDeletion = false;
    bool requireLinearHistory = false;
    std::set<MergeStrategy> allowedMergeStrategies{
        MergeStrategy::Squash,
        MergeStrategy::Rebase
    };
    std::set<std::string> bypassUsers;
};

struct PullRequest {
    int number;
    std::string title;
    std::string sourceBranch;
    std::string targetBranch;
    std::string author;
    PullRequestState state;
    std::vector<Commit> commits;
    std::vector<Review> reviews;
    std::map<std::string, StatusCheck> checks;
    int unresolvedConversations = 0;
    bool mergeConflicts = false;
    MergeStrategy mergeStrategy = MergeStrategy::Squash;
    std::string baseShaAtCreation;
    std::string currentBaseSha;

    const Commit* latestCommit() const {
        if (commits.empty()) {
            return nullptr;
        }
        return &commits.back();
    }
};

struct MergeDecision {
    bool allowed;
    std::vector<std::string> reasons;
};

class Repository {
private:
    std::string name_;
    std::map<std::string, std::string> branches_;
    std::map<std::string, BranchProtection> protections_;
    std::map<int, PullRequest> pullRequests_;
    int nextPrNumber_ = 1;

    PullRequest& getPullRequest(int number) {
        auto it = pullRequests_.find(number);
        if (it == pullRequests_.end()) {
            throw std::runtime_error("Unknown Pull Request");
        }
        return it->second;
    }

    const PullRequest& getPullRequest(int number) const {
        auto it = pullRequests_.find(number);
        if (it == pullRequests_.end()) {
            throw std::runtime_error("Unknown Pull Request");
        }
        return it->second;
    }

public:
    explicit Repository(std::string name)
        : name_(std::move(name)) {}

    void createBranch(const std::string& name, const std::string& sha) {
        if (name.empty() || sha.empty()) {
            throw std::invalid_argument("Branch name and SHA are required");
        }

        if (branches_.contains(name)) {
            throw std::runtime_error("Branch already exists");
        }

        branches_[name] = sha;
    }

    void updateBranch(const std::string& name, const std::string& sha) {
        if (!branches_.contains(name)) {
            throw std::runtime_error("Unknown branch");
        }

        if (sha.empty()) {
            throw std::invalid_argument("Commit SHA cannot be empty");
        }

        branches_[name] = sha;
    }

    void protectBranch(BranchProtection policy) {
        if (!branches_.contains(policy.branch)) {
            throw std::runtime_error("Cannot protect unknown branch");
        }

        protections_[policy.branch] = std::move(policy);
    }

    int createPullRequest(
        const std::string& title,
        const std::string& sourceBranch,
        const std::string& targetBranch,
        const std::string& author,
        bool draft
    ) {
        if (title.empty() || author.empty()) {
            throw std::invalid_argument("Title and author are required");
        }

        if (!branches_.contains(sourceBranch) ||
            !branches_.contains(targetBranch)) {
            throw std::runtime_error("Source or target branch does not exist");
        }

        if (sourceBranch == targetBranch) {
            throw std::invalid_argument(
                "Source and target branches must differ"
            );
        }

        int number = nextPrNumber_++;
        std::string baseSha = branches_.at(targetBranch);

        pullRequests_.emplace(
            number,
            PullRequest{
                number,
                title,
                sourceBranch,
                targetBranch,
                author,
                draft ? PullRequestState::Draft : PullRequestState::Open,
                {},
                {},
                {},
                0,
                false,
                MergeStrategy::Squash,
                baseSha,
                baseSha
            }
        );

        return number;
    }

    void addCommit(int number, Commit commit) {
        PullRequest& pr = getPullRequest(number);

        if (pr.state != PullRequestState::Draft &&
            pr.state != PullRequestState::Open) {
            throw std::runtime_error("Inactive Pull Request");
        }

        if (commit.sha.empty() || commit.message.empty()) {
            throw std::invalid_argument("Commit SHA and message are required");
        }

        pr.commits.push_back(commit);
        updateBranch(pr.sourceBranch, commit.sha);

        /*
         * Governance evaluates reviews and checks against the commit they
         * actually inspected. A new commit therefore makes older evidence
         * stale when the policy requires current-commit validation.
         */
        auto protection = protections_.find(pr.targetBranch);
        if (protection != protections_.end() &&
            protection->second.dismissStaleReviews) {
            pr.reviews.erase(
                std::remove_if(
                    pr.reviews.begin(),
                    pr.reviews.end(),
                    [&](const Review& review) {
                        return review.commitSha != commit.sha;
                    }
                ),
                pr.reviews.end()
            );
        }

        pr.checks.clear();
    }

    void markReady(int number) {
        PullRequest& pr = getPullRequest(number);

        if (pr.state != PullRequestState::Draft) {
            throw std::runtime_error("Only drafts can become ready");
        }

        pr.state = PullRequestState::Open;
    }

    void submitReview(
        int number,
        const std::string& reviewer,
        ReviewState state
    ) {
        PullRequest& pr = getPullRequest(number);

        if (pr.state != PullRequestState::Open) {
            throw std::runtime_error("Review requires an open Pull Request");
        }

        if (reviewer.empty() || reviewer == pr.author) {
            throw std::invalid_argument(
                "Reviewer must be present and different from author"
            );
        }

        const Commit* latest = pr.latestCommit();
        if (latest == nullptr) {
            throw std::runtime_error("Cannot review a PR without commits");
        }

        pr.reviews.push_back(
            Review{
                reviewer,
                state,
                latest->sha
            }
        );
    }

    void setStatusCheck(
        int number,
        const std::string& name,
        CheckState state
    ) {
        PullRequest& pr = getPullRequest(number);
        const Commit* latest = pr.latestCommit();

        if (latest == nullptr) {
            throw std::runtime_error("Status check requires a commit");
        }

        if (name.empty()) {
            throw std::invalid_argument("Status check name is required");
        }

        pr.checks[name] = StatusCheck{
            name,
            state,
            latest->sha
        };
    }

    void addConversation(int number) {
        PullRequest& pr = getPullRequest(number);
        ++pr.unresolvedConversations;
    }

    void resolveConversation(int number) {
        PullRequest& pr = getPullRequest(number);

        if (pr.unresolvedConversations == 0) {
            throw std::runtime_error("No unresolved conversations");
        }

        --pr.unresolvedConversations;
    }

    void synchronizeBase(int number, const std::string& newBaseSha) {
        PullRequest& pr = getPullRequest(number);

        if (newBaseSha.empty()) {
            throw std::invalid_argument("Base SHA is required");
        }

        pr.currentBaseSha = newBaseSha;

        /*
         * This compact model treats a changed base as a possible conflict.
         * A production Git implementation would inspect the actual commit
         * graph and perform a three-way merge.
         */
        pr.mergeConflicts = newBaseSha != pr.baseShaAtCreation;

        auto protection = protections_.find(pr.targetBranch);
        if (protection != protections_.end() &&
            protection->second.dismissStaleReviews) {
            const Commit* latest = pr.latestCommit();

            if (latest != nullptr) {
                pr.reviews.erase(
                    std::remove_if(
                        pr.reviews.begin(),
                        pr.reviews.end(),
                        [&](const Review& review) {
                            return review.commitSha != latest->sha;
                        }
                    ),
                    pr.reviews.end()
                );
            }
        }
    }

    MergeDecision evaluateMerge(
        int number,
        const std::string& actor
    ) const {
        const PullRequest& pr = getPullRequest(number);
        std::vector<std::string> reasons;

        auto protectionIt = protections_.find(pr.targetBranch);

        if (protectionIt == protections_.end()) {
            return {
                false,
                {"Target branch has no branch-protection policy"}
            };
        }

        const BranchProtection& policy = protectionIt->second;

        if (policy.bypassUsers.contains(actor)) {
            return {
                true,
                {"Configured governance bypass permits the merge"}
            };
        }

        if (pr.state != PullRequestState::Open) {
            reasons.push_back("Pull Request is not open");
        }

        const Commit* latest = pr.latestCommit();

        if (latest == nullptr) {
            reasons.push_back("Pull Request has no commits");
        }

        if (pr.mergeConflicts) {
            reasons.push_back("Merge conflicts remain unresolved");
        }

        if (!policy.allowedMergeStrategies.contains(pr.mergeStrategy)) {
            reasons.push_back(
                "Selected merge strategy is not permitted"
            );
        }

        std::set<std::string> approvals;

        if (latest != nullptr) {
            for (const Review& review : pr.reviews) {
                if (review.commitSha != latest->sha) {
                    continue;
                }

                if (review.state == ReviewState::Approved) {
                    approvals.insert(review.reviewer);
                } else if (review.state == ReviewState::ChangesRequested) {
                    approvals.erase(review.reviewer);
                }
            }
        }

        if (approvals.size() < policy.requiredReviews) {
            std::ostringstream message;
            message << "Required approvals: "
                    << policy.requiredReviews
                    << "; current approvals: "
                    << approvals.size();
            reasons.push_back(message.str());
        }

        if (latest != nullptr) {
            for (const std::string& requiredCheck : policy.requiredChecks) {
                auto checkIt = pr.checks.find(requiredCheck);

                if (checkIt == pr.checks.end()) {
                    reasons.push_back(
                        "Missing required status check: " + requiredCheck
                    );
                    continue;
                }

                if (checkIt->second.commitSha != latest->sha) {
                    reasons.push_back(
                        "Stale required status check: " + requiredCheck
                    );
                } else if (checkIt->second.state != CheckState::Passed) {
                    reasons.push_back(
                        "Required status check failed: " + requiredCheck
                    );
                }
            }
        }

        if (policy.requireConversationResolution &&
            pr.unresolvedConversations > 0) {
            reasons.push_back(
                "Unresolved review conversations remain"
            );
        }

        if (policy.requireLinearHistory &&
            pr.mergeStrategy == MergeStrategy::MergeCommit) {
            reasons.push_back(
                "Merge commits are incompatible with linear-history policy"
            );
        }

        return {
            reasons.empty(),
            reasons
        };
    }

    void merge(int number, const std::string& actor) {
        MergeDecision decision = evaluateMerge(number, actor);

        if (!decision.allowed) {
            std::ostringstream message;
            message << "Merge blocked:";

            for (const std::string& reason : decision.reasons) {
                message << " " << reason << ";";
            }

            throw std::runtime_error(message.str());
        }

        PullRequest& pr = getPullRequest(number);
        const Commit* latest = pr.latestCommit();

        if (latest == nullptr) {
            throw std::runtime_error("Invariant failure: missing latest commit");
        }

        std::string result =
            "merge-" +
            std::to_string(pr.number) +
            "-" +
            latest->sha.substr(0, std::min<std::size_t>(8, latest->sha.size())) +
            "-" +
            toString(pr.mergeStrategy);

        branches_[pr.targetBranch] = result;
        pr.state = PullRequestState::Merged;
    }

    void close(int number) {
        PullRequest& pr = getPullRequest(number);

        if (pr.state == PullRequestState::Merged) {
            throw std::runtime_error("Merged PR cannot be closed");
        }

        pr.state = PullRequestState::Closed;
    }

    void reopen(int number) {
        PullRequest& pr = getPullRequest(number);

        if (pr.state != PullRequestState::Closed) {
            throw std::runtime_error("Only closed PRs can be reopened");
        }

        pr.state = PullRequestState::Open;
    }

    const std::string& branchSha(const std::string& branch) const {
        auto it = branches_.find(branch);

        if (it == branches_.end()) {
            throw std::runtime_error("Unknown branch");
        }

        return it->second;
    }
};

void printDecision(
    const Repository& repository,
    int prNumber,
    const std::string& actor
) {
    MergeDecision decision = repository.evaluateMerge(prNumber, actor);

    std::cout
        << "PR #" << prNumber
        << ": "
        << (decision.allowed ? "MERGEABLE" : "BLOCKED")
        << "\n";

    for (const std::string& reason : decision.reasons) {
        std::cout << "  - " << reason << "\n";
    }
}

int main() {
    try {
        Repository repository("payments-platform");

        repository.createBranch("main", "base-001");
        repository.createBranch(
            "feature/payment-controls",
            "base-001"
        );

        repository.protectBranch(
            BranchProtection{
                "main",
                2,
                {"unit-tests", "security-scan"},
                true,
                true,
                true,
                false,
                false,
                true,
                {MergeStrategy::Squash, MergeStrategy::Rebase},
                {}
            }
        );

        int pr = repository.createPullRequest(
            "Strengthen payment controls",
            "feature/payment-controls",
            "main",
            "alice",
            true
        );

        repository.addCommit(
            pr,
            {"commit-001", "Validate transaction limits", "alice"}
        );

        repository.markReady(pr);

        repository.submitReview(
            pr,
            "bob",
            ReviewState::Approved
        );

        repository.submitReview(
            pr,
            "carol",
            ReviewState::Approved
        );

        repository.setStatusCheck(
            pr,
            "unit-tests",
            CheckState::Passed
        );

        repository.setStatusCheck(
            pr,
            "security-scan",
            CheckState::Passed
        );

        repository.addConversation(pr);
        printDecision(repository, pr, "release-manager");

        repository.resolveConversation(pr);
        printDecision(repository, pr, "release-manager");

        repository.merge(pr, "release-manager");

        std::cout
            << "main after merge: "
            << repository.branchSha("main")
            << "\n\n";

        /*
         * Second scenario demonstrates why approval evidence is tied to
         * the reviewed commit rather than merely to the Pull Request.
         */
        repository.createBranch(
            "feature/audit",
            repository.branchSha("main")
        );

        int auditPr = repository.createPullRequest(
            "Add audit records",
            "feature/audit",
            "main",
            "diana",
            false
        );

        repository.addCommit(
            auditPr,
            {"commit-002", "Create audit model", "diana"}
        );

        repository.submitReview(
            auditPr,
            "erin",
            ReviewState::Approved
        );

        repository.submitReview(
            auditPr,
            "frank",
            ReviewState::Approved
        );

        repository.setStatusCheck(
            auditPr,
            "unit-tests",
            CheckState::Passed
        );

        repository.setStatusCheck(
            auditPr,
            "security-scan",
            CheckState::Passed
        );

        repository.addCommit(
            auditPr,
            {"commit-003", "Handle audit persistence failure", "diana"}
        );

        printDecision(repository, auditPr, "release-manager");

        repository.submitReview(
            auditPr,
            "erin",
            ReviewState::Approved
        );

        repository.submitReview(
            auditPr,
            "frank",
            ReviewState::Approved
        );

        repository.setStatusCheck(
            auditPr,
            "unit-tests",
            CheckState::Passed
        );

        repository.setStatusCheck(
            auditPr,
            "security-scan",
            CheckState::Passed
        );

        printDecision(repository, auditPr, "release-manager");
        repository.merge(auditPr, "release-manager");

        std::cout
            << "Audit PR state: "
            << toString(PullRequestState::Merged)
            << "\n";
    }
    catch (const std::exception& error) {
        std::cerr << "Governance error: "
                  << error.what()
                  << "\n";
        return 1;
    }

    return 0;
}
