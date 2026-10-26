#include <algorithm>
#include <exception>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

enum class PRState {
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
    Passing,
    Failing,
    Pending
};

enum class MergeStrategy {
    Merge,
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
};

struct ReviewConversation {
    int id;
    std::string reviewer;
    std::string body;
    bool resolved{false};
};

struct StatusCheck {
    std::string name;
    CheckState state;
};

struct BranchProtection {
    int requiredApprovals{2};
    std::set<std::string> requiredChecks;
    bool requireResolvedConversations{true};
    bool restrictDirectPush{true};
    bool restrictForcePush{true};
    bool restrictDeletion{true};
    bool requireLinearHistory{false};
    bool allowAdministratorBypass{false};
};

struct Branch {
    std::string name;
    bool protectedBranch{false};
    std::string headSha;
    std::vector<Commit> commits;
};

struct PullRequest {
    int number;
    std::string author;
    std::string sourceBranch;
    std::string targetBranch;
    std::string title;
    PRState state{PRState::Open};
    bool draft{false};
    std::vector<Commit> commits;
    std::vector<Review> reviews;
    std::vector<ReviewConversation> conversations;
    std::map<std::string, StatusCheck> checks;
    std::string baseShaAtOpen;
};

class GovernanceError : public std::runtime_error {
public:
    explicit GovernanceError(const std::string& message)
        : std::runtime_error(message) {}
};

class MergeEligibilityEngine {
public:
    explicit MergeEligibilityEngine(BranchProtection protection)
        : protection_(std::move(protection)) {}

    void addBranch(const Branch& branch) {
        if (branch.name.empty()) {
            throw GovernanceError("Branch name cannot be empty.");
        }

        if (branches_.contains(branch.name)) {
            throw GovernanceError("Branch already exists.");
        }

        branches_.emplace(branch.name, branch);
    }

    void addEligibleReviewer(const std::string& reviewer) {
        if (reviewer.empty()) {
            throw GovernanceError("Reviewer cannot be empty.");
        }

        reviewers_.insert(reviewer);
    }

    PullRequest& createPullRequest(
        int number,
        const std::string& author,
        const std::string& source,
        const std::string& target,
        const std::string& title,
        bool draft
    ) {
        if (number <= 0) {
            throw GovernanceError("Pull Request number must be positive.");
        }

        if (pullRequests_.contains(number)) {
            throw GovernanceError("Pull Request number already exists.");
        }

        if (!branches_.contains(source) || !branches_.contains(target)) {
            throw GovernanceError("Both branches must exist.");
        }

        if (source == target) {
            throw GovernanceError("Source and target branches must differ.");
        }

        if (title.empty()) {
            throw GovernanceError("Pull Request title cannot be empty.");
        }

        PullRequest pr{
            number,
            author,
            source,
            target,
            title,
            draft ? PRState::Draft : PRState::Open,
            draft,
            {},
            {},
            {},
            {},
            branches_.at(target).headSha
        };

        auto [iterator, inserted] = pullRequests_.emplace(number, std::move(pr));
        return iterator->second;
    }

    void publish(PullRequest& pr) {
        if (!pr.draft) {
            return;
        }

        pr.draft = false;
        pr.state = PRState::Open;
    }

    void addCommit(PullRequest& pr, Commit commit) {
        if (pr.state != PRState::Open) {
            throw GovernanceError("Commits require an open Pull Request.");
        }

        if (commit.sha.size() < 7) {
            throw GovernanceError("Commit SHA is too short.");
        }

        if (std::any_of(
                pr.commits.begin(),
                pr.commits.end(),
                [&](const Commit& existing) {
                    return existing.sha == commit.sha;
                })) {
            throw GovernanceError("Duplicate commit.");
        }

        pr.commits.push_back(commit);

        Branch& source = branches_.at(pr.sourceBranch);
        source.commits.push_back(commit);
        source.headSha = commit.sha;
    }

    void submitReview(
        PullRequest& pr,
        const std::string& reviewer,
        ReviewState state,
        const std::string& commitSha
    ) {
        if (pr.state != PRState::Open) {
            throw GovernanceError("Review requires an open Pull Request.");
        }

        if (reviewer == pr.author) {
            throw GovernanceError("Self-approval is not allowed.");
        }

        if (!reviewers_.contains(reviewer)) {
            throw GovernanceError("Reviewer is not eligible.");
        }

        if (commitSha.empty()) {
            throw GovernanceError("Review must reference a commit.");
        }

        pr.reviews.push_back({reviewer, state, commitSha});
    }

    int addConversation(
        PullRequest& pr,
        const std::string& reviewer,
        const std::string& body
    ) {
        if (reviewer.empty() || body.empty()) {
            throw GovernanceError("Conversation reviewer and body are required.");
        }

        int id = nextConversationId_++;
        pr.conversations.push_back({id, reviewer, body, false});
        return id;
    }

    void resolveConversation(PullRequest& pr, int id) {
        auto iterator = std::find_if(
            pr.conversations.begin(),
            pr.conversations.end(),
            [&](const ReviewConversation& conversation) {
                return conversation.id == id;
            }
        );

        if (iterator == pr.conversations.end()) {
            throw GovernanceError("Conversation does not exist.");
        }

        iterator->resolved = true;
    }

    void setCheck(
        PullRequest& pr,
        const std::string& name,
        CheckState state
    ) {
        if (name.empty()) {
            throw GovernanceError("Status check name cannot be empty.");
        }

        pr.checks[name] = StatusCheck{name, state};
    }

    void synchronizeBase(PullRequest& pr) {
        Branch& target = branches_.at(pr.targetBranch);
        pr.baseShaAtOpen = target.headSha;

        for (Review& review : pr.reviews) {
            if (review.state == ReviewState::Approved) {
                review.state = ReviewState::Dismissed;
            }
        }
    }

    std::vector<std::string> evaluate(const PullRequest& pr) const {
        std::vector<std::string> failures;

        if (pr.state != PRState::Open) {
            failures.push_back("Pull Request is not open.");
        }

        if (pr.draft) {
            failures.push_back("Pull Request is still a draft.");
        }

        if (pr.commits.empty()) {
            failures.push_back("Pull Request contains no commits.");
        }

        std::set<std::string> approvals;

        for (const Review& review : pr.reviews) {
            if (review.state == ReviewState::ChangesRequested) {
                failures.push_back(
                    "Reviewer " + review.reviewer + " requested changes."
                );
            }

            if (review.state == ReviewState::Approved &&
                reviewers_.contains(review.reviewer)) {
                approvals.insert(review.reviewer);
            }
        }

        if (static_cast<int>(approvals.size()) <
            protection_.requiredApprovals) {
            failures.push_back(
                "Required approvals have not been satisfied."
            );
        }

        for (const std::string& required : protection_.requiredChecks) {
            auto iterator = pr.checks.find(required);

            if (iterator == pr.checks.end()) {
                failures.push_back(
                    "Required check '" + required + "' is missing."
                );
                continue;
            }

            if (iterator->second.state != CheckState::Passing) {
                failures.push_back(
                    "Required check '" + required + "' is not passing."
                );
            }
        }

        if (protection_.requireResolvedConversations) {
            for (const auto& conversation : pr.conversations) {
                if (!conversation.resolved) {
                    failures.push_back(
                        "Unresolved review conversation remains."
                    );
                    break;
                }
            }
        }

        const Branch& target = branches_.at(pr.targetBranch);

        if (target.headSha != pr.baseShaAtOpen) {
            failures.push_back("Base branch is out of date.");
        }

        return failures;
    }

    std::string merge(
        PullRequest& pr,
        MergeStrategy strategy
    ) {
        const std::vector<std::string> failures = evaluate(pr);

        if (!failures.empty()) {
            throw GovernanceError(formatFailures(failures));
        }

        Branch& target = branches_.at(pr.targetBranch);

        std::string prefix;

        switch (strategy) {
            case MergeStrategy::Merge:
                prefix = "merge";
                break;
            case MergeStrategy::Squash:
                prefix = "squash";
                break;
            case MergeStrategy::Rebase:
                prefix = "rebase";
                break;
        }

        const std::string mergeSha =
            prefix + "-pr-" + std::to_string(pr.number);

        target.commits.push_back({
            mergeSha,
            "Integrate PR #" + std::to_string(pr.number) +
                ": " + pr.title,
            pr.author
        });

        target.headSha = mergeSha;
        pr.state = PRState::Merged;

        return mergeSha;
    }

    void close(PullRequest& pr) {
        if (pr.state == PRState::Merged) {
            throw GovernanceError(
                "Merged Pull Request cannot be closed."
            );
        }

        pr.state = PRState::Closed;
    }

    void reopen(PullRequest& pr) {
        if (pr.state != PRState::Closed) {
            throw GovernanceError(
                "Only closed Pull Requests can be reopened."
            );
        }

        pr.state = PRState::Open;
    }

private:
    BranchProtection protection_;
    std::map<std::string, Branch> branches_;
    std::set<std::string> reviewers_;
    std::map<int, PullRequest> pullRequests_;
    int nextConversationId_{1};

    static std::string formatFailures(
        const std::vector<std::string>& failures
    ) {
        std::string message = "Merge blocked:";

        for (const std::string& failure : failures) {
            message += "\n- " + failure;
        }

        return message;
    }
};

int main() {
    try {
        BranchProtection protection;
        protection.requiredApprovals = 2;
        protection.requiredChecks = {
            "unit-tests",
            "security-scan"
        };
        protection.requireResolvedConversations = true;
        protection.restrictDirectPush = true;
        protection.restrictForcePush = true;
        protection.restrictDeletion = true;
        protection.requireLinearHistory = true;

        MergeEligibilityEngine engine(protection);

        engine.addBranch({
            "main",
            true,
            "main-base-001",
            {}
        });

        engine.addBranch({
            "feature/refund-validation",
            false,
            "feature-base-001",
            {}
        });

        engine.addEligibleReviewer("alice");
        engine.addEligibleReviewer("bob");
        engine.addEligibleReviewer("carol");

        PullRequest& pr = engine.createPullRequest(
            77,
            "developer",
            "feature/refund-validation",
            "main",
            "Validate refund requests",
            true
        );

        engine.addCommit(
            pr,
            {
                "abcdef1234567",
                "Add refund validation",
                "developer"
            }
        );

        const int conversationId = engine.addConversation(
            pr,
            "alice",
            "Add a boundary test for zero-value refunds."
        );

        engine.setCheck(pr, "unit-tests", CheckState::Passing);
        engine.setCheck(pr, "security-scan", CheckState::Passing);

        std::vector<std::string> initialFailures = engine.evaluate(pr);

        std::cout << "Initial eligibility:\n";

        for (const std::string& failure : initialFailures) {
            std::cout << "  BLOCKED: " << failure << '\n';
        }

        engine.publish(pr);

        engine.submitReview(
            pr,
            "alice",
            ReviewState::Approved,
            "abcdef1234567"
        );

        engine.submitReview(
            pr,
            "bob",
            ReviewState::Approved,
            "abcdef1234567"
        );

        engine.resolveConversation(pr, conversationId);

        std::vector<std::string> finalFailures = engine.evaluate(pr);

        std::cout << "\nFinal eligibility: "
                  << (finalFailures.empty() ? "eligible" : "blocked")
                  << '\n';

        if (finalFailures.empty()) {
            std::string mergeSha =
                engine.merge(pr, MergeStrategy::Squash);

            std::cout << "Merged using squash strategy: "
                      << mergeSha << '\n';
        }

        std::cout << "Final Pull Request state: "
                  << (pr.state == PRState::Merged ? "merged" : "not merged")
                  << '\n';

        try {
            engine.reopen(pr);
        } catch (const GovernanceError& error) {
            std::cout << "Expected transition failure: "
                      << error.what() << '\n';
        }
    } catch (const std::exception& error) {
        std::cerr << "Fatal governance error: "
                  << error.what() << '\n';
        return 1;
    }

    return 0;
}
