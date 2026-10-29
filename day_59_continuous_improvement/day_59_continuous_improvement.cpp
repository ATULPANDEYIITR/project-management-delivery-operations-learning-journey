#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

enum class PullRequestState { Draft, Open, Closed, Merged };
enum class ReviewState { Commented, Approved, ChangesRequested, Dismissed };
enum class CheckState { Pending, Success, Failure };

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
        case CheckState::Success: return "success";
        case CheckState::Failure: return "failure";
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
    std::vector<std::string> comments;
};

struct StatusCheck {
    std::string name;
    CheckState state;
    std::string commitSha;
};

struct BranchProtection {
    int requiredApprovals{0};
    std::set<std::string> requiredChecks;
    bool requireResolvedConversations{true};
    bool dismissStaleApprovals{true};
    bool requireLinearHistory{false};
    bool allowDirectPush{false};
    bool allowForcePush{false};
    bool allowBranchDeletion{false};
};

struct Branch {
    std::string name;
    bool protectedBranch{false};
    std::vector<Commit> commits;
};

struct PullRequest {
    int number{};
    std::string title;
    std::string source;
    std::string target;
    std::string author;
    PullRequestState state{PullRequestState::Open};
    bool draft{false};
    std::vector<Commit> proposedCommits;
    std::vector<Review> reviews;
    std::vector<StatusCheck> checks;
    int unresolvedConversations{0};

    std::optional<std::string> head() const {
        if (proposedCommits.empty()) return std::nullopt;
        return proposedCommits.back().sha;
    }
};

struct Eligibility {
    bool eligible{false};
    std::vector<std::string> reasons;
};

class GovernanceEngine {
private:
    std::map<std::string, Branch> branches;
    std::map<std::string, BranchProtection> protections;
    std::map<int, PullRequest> pullRequests;
    int nextPR{1};

    Branch& branch(const std::string& name) {
        auto it = branches.find(name);
        if (it == branches.end()) {
            throw std::runtime_error("Unknown branch: " + name);
        }
        return it->second;
    }

    PullRequest& pullRequest(int number) {
        auto it = pullRequests.find(number);
        if (it == pullRequests.end()) {
            throw std::runtime_error("Unknown pull request");
        }
        return it->second;
    }

    static void ensureActive(const PullRequest& pr) {
        if (pr.state != PullRequestState::Open &&
            pr.state != PullRequestState::Draft) {
            throw std::runtime_error("Pull request is not active");
        }
    }

public:
    void addBranch(const std::string& name, bool protectedBranch = false) {
        if (name.empty()) throw std::runtime_error("Branch name is empty");
        if (branches.count(name)) {
            throw std::runtime_error("Duplicate branch: " + name);
        }
        branches.emplace(name, Branch{name, protectedBranch, {}});
    }

    void addCommit(
        const std::string& branchName,
        const std::string& sha,
        const std::string& message,
        const std::string& author
    ) {
        Branch& b = branch(branchName);

        if (sha.size() < 7) {
            throw std::runtime_error("Commit SHA is too short");
        }
        if (message.empty() || author.empty()) {
            throw std::runtime_error("Commit message and author are required");
        }

        const bool duplicate = std::any_of(
            b.commits.begin(),
            b.commits.end(),
            [&](const Commit& c) { return c.sha == sha; }
        );

        if (duplicate) {
            throw std::runtime_error("Duplicate commit SHA");
        }

        b.commits.push_back({sha, message, author});
    }

    void protectBranch(
        const std::string& name,
        const BranchProtection& policy
    ) {
        Branch& b = branch(name);
        if (policy.requiredApprovals < 0) {
            throw std::runtime_error("Invalid approval requirement");
        }

        b.protectedBranch = true;
        protections[name] = policy;
    }

    int createPullRequest(
        const std::string& title,
        const std::string& source,
        const std::string& target,
        const std::string& author,
        bool draft = false
    ) {
        if (source == target) {
            throw std::runtime_error("Source and target must differ");
        }

        Branch& sourceBranch = branch(source);
        branch(target);

        if (sourceBranch.commits.empty()) {
            throw std::runtime_error("Source branch contains no changes");
        }

        if (title.empty() || author.empty()) {
            throw std::runtime_error("Title and author are required");
        }

        PullRequest pr;
        pr.number = nextPR++;
        pr.title = title;
        pr.source = source;
        pr.target = target;
        pr.author = author;
        pr.draft = draft;
        pr.state = draft ? PullRequestState::Draft : PullRequestState::Open;
        pr.proposedCommits = sourceBranch.commits;

        pullRequests.emplace(pr.number, std::move(pr));
        return nextPR - 1;
    }

    void addConversation(int number) {
        PullRequest& pr = pullRequest(number);
        ensureActive(pr);
        ++pr.unresolvedConversations;
    }

    void resolveConversation(int number) {
        PullRequest& pr = pullRequest(number);
        if (pr.unresolvedConversations == 0) {
            throw std::runtime_error("No unresolved conversation exists");
        }
        --pr.unresolvedConversations;
    }

    void submitReview(
        int number,
        const std::string& reviewer,
        ReviewState state,
        const std::vector<std::string>& comments = {}
    ) {
        PullRequest& pr = pullRequest(number);
        ensureActive(pr);

        if (reviewer.empty()) {
            throw std::runtime_error("Reviewer identity is required");
        }

        if (state == ReviewState::Approved && reviewer == pr.author) {
            throw std::runtime_error("Self-approval is prohibited");
        }

        auto head = pr.head();
        if (!head) {
            throw std::runtime_error("Cannot review a PR without a head");
        }

        pr.reviews.push_back({
            reviewer,
            state,
            *head,
            comments
        });
    }

    void updateCheck(
        int number,
        const std::string& name,
        CheckState state
    ) {
        PullRequest& pr = pullRequest(number);
        ensureActive(pr);

        if (name.empty()) {
            throw std::runtime_error("Check name is required");
        }

        auto head = pr.head();
        if (!head) {
            throw std::runtime_error("No head commit exists");
        }

        auto it = std::find_if(
            pr.checks.begin(),
            pr.checks.end(),
            [&](const StatusCheck& check) {
                return check.name == name && check.commitSha == *head;
            }
        );

        if (it != pr.checks.end()) {
            it->state = state;
        } else {
            pr.checks.push_back({name, state, *head});
        }
    }

    void synchronize(int number) {
        PullRequest& pr = pullRequest(number);
        ensureActive(pr);

        const Branch& source = branch(pr.source);
        pr.proposedCommits = source.commits;

        auto policyIt = protections.find(pr.target);
        if (policyIt == protections.end()) return;

        if (!policyIt->second.dismissStaleApprovals) return;

        auto head = pr.head();
        for (Review& review : pr.reviews) {
            if (review.state == ReviewState::Approved &&
                review.commitSha != *head) {
                review.state = ReviewState::Dismissed;
            }
        }
    }

    Eligibility evaluate(int number) const {
        const auto prIt = pullRequests.find(number);
        if (prIt == pullRequests.end()) {
            throw std::runtime_error("Unknown pull request");
        }

        const PullRequest& pr = prIt->second;
        Eligibility result;

        if (pr.state != PullRequestState::Open) {
            result.reasons.push_back("Pull request is not open");
        }

        if (pr.draft) {
            result.reasons.push_back("Pull request is a draft");
        }

        auto head = pr.head();
        if (!head) {
            result.reasons.push_back("No proposed commit exists");
        }

        BranchProtection policy;
        auto policyIt = protections.find(pr.target);
        if (policyIt != protections.end()) {
            policy = policyIt->second;
        } else {
            policy.requiredApprovals = 0;
            policy.requireResolvedConversations = false;
        }

        std::set<std::string> approvals;

        for (const Review& review : pr.reviews) {
            if (review.state == ReviewState::Approved &&
                review.commitSha == *head &&
                review.reviewer != pr.author) {
                approvals.insert(review.reviewer);
            }
        }

        if (static_cast<int>(approvals.size()) < policy.requiredApprovals) {
            result.reasons.push_back(
                "Required approvals: " +
                std::to_string(policy.requiredApprovals) +
                ", current approvals: " +
                std::to_string(approvals.size())
            );
        }

        for (const std::string& required : policy.requiredChecks) {
            bool success = false;

            for (const StatusCheck& check : pr.checks) {
                if (check.name == required &&
                    check.commitSha == *head &&
                    check.state == CheckState::Success) {
                    success = true;
                    break;
                }
            }

            if (!success) {
                result.reasons.push_back(
                    "Required check is missing or unsuccessful: " + required
                );
            }
        }

        if (policy.requireResolvedConversations &&
            pr.unresolvedConversations > 0) {
            result.reasons.push_back(
                "Unresolved conversations: " +
                std::to_string(pr.unresolvedConversations)
            );
        }

        result.eligible = result.reasons.empty();
        return result;
    }

    void merge(int number) {
        PullRequest& pr = pullRequest(number);
        Eligibility eligibility = evaluate(number);

        if (!eligibility.eligible) {
            throw std::runtime_error("Merge blocked");
        }

        Branch& target = branch(pr.target);
        const Branch& source = branch(pr.source);

        for (const Commit& sourceCommit : source.commits) {
            auto found = std::find_if(
                target.commits.begin(),
                target.commits.end(),
                [&](const Commit& targetCommit) {
                    return targetCommit.sha == sourceCommit.sha;
                }
            );

            if (found == target.commits.end()) {
                target.commits.push_back(sourceCommit);
            }
        }

        pr.state = PullRequestState::Merged;
    }

    void printReport(int number) const {
        const PullRequest& pr = pullRequests.at(number);
        const Eligibility e = evaluate(number);

        std::cout << "\nPR #" << pr.number << " - " << pr.title << "\n";
        std::cout << "Source: " << pr.source
                  << " -> Target: " << pr.target << "\n";
        std::cout << "State: " << toString(pr.state) << "\n";
        std::cout << "Merge eligible: "
                  << (e.eligible ? "yes" : "no") << "\n";

        if (!e.reasons.empty()) {
            std::cout << "Blocking conditions:\n";
            for (const std::string& reason : e.reasons) {
                std::cout << "  - " << reason << "\n";
            }
        }
    }
};

int main() {
    try {
        GovernanceEngine engine;

        engine.addBranch("main", true);
        engine.addBranch("improvement/cycle-time");
        engine.addBranch("improvement/review-quality");

        engine.addCommit(
            "main",
            "a100001",
            "Establish repository baseline",
            "platform"
        );

        engine.addCommit(
            "improvement/cycle-time",
            "b100001",
            "Measure pull request cycle time",
            "developer-1"
        );

        engine.addCommit(
            "improvement/cycle-time",
            "b100002",
            "Add process metrics",
            "developer-1"
        );

        BranchProtection protection;
        protection.requiredApprovals = 2;
        protection.requiredChecks = {"unit-tests", "security-scan"};
        protection.requireResolvedConversations = true;
        protection.dismissStaleApprovals = true;
        protection.requireLinearHistory = true;
        protection.allowDirectPush = false;
        protection.allowForcePush = false;

        engine.protectBranch("main", protection);

        int pr = engine.createPullRequest(
            "Reduce pull request cycle time",
            "improvement/cycle-time",
            "main",
            "developer-1"
        );

        engine.addConversation(pr);
        engine.submitReview(pr, "reviewer-1", ReviewState::Approved);
        engine.submitReview(
            pr,
            "reviewer-2",
            ReviewState::ChangesRequested,
            {"Metric definition needs clarification"}
        );

        engine.updateCheck(pr, "unit-tests", CheckState::Success);
        engine.updateCheck(pr, "security-scan", CheckState::Success);

        engine.printReport(pr);

        engine.resolveConversation(pr);
        engine.submitReview(pr, "reviewer-2", ReviewState::Approved);

        if (!engine.evaluate(pr).eligible) {
            throw std::runtime_error("Expected PR to be merge eligible");
        }

        engine.merge(pr);
        engine.printReport(pr);

        int secondPR = engine.createPullRequest(
            "Improve review quality measurement",
            "improvement/review-quality",
            "main",
            "developer-2"
        );

        engine.submitReview(secondPR, "reviewer-1", ReviewState::Approved);
        engine.submitReview(secondPR, "reviewer-2", ReviewState::Approved);
        engine.updateCheck(secondPR, "unit-tests", CheckState::Success);
        engine.updateCheck(secondPR, "security-scan", CheckState::Success);

        engine.addCommit(
            "improvement/review-quality",
            "c100001",
            "Correct review metric calculation",
            "developer-2"
        );

        engine.synchronize(secondPR);

        engine.printReport(secondPR);

        if (engine.evaluate(secondPR).eligible) {
            throw std::runtime_error(
                "Stale approvals should prevent merge eligibility"
            );
        }

    } catch (const std::exception& ex) {
        std::cerr << "Governance error: " << ex.what() << '\n';
        return 1;
    }

    return 0;
}
