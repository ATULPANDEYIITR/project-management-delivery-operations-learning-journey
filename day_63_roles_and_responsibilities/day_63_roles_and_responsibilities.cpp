#include <algorithm>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

enum class PRState { Draft, Open, Closed, Merged };
enum class ReviewState { Commented, Approved, ChangesRequested, Dismissed };
enum class CheckState { Passing, Failing, Pending };

struct Person {
    std::string username;
    std::unordered_set<std::string> roles;
};

struct Commit {
    std::string sha;
    std::string message;
    std::string author;
};

struct Review {
    std::string reviewer;
    ReviewState state;
    std::string commit_sha;
};

struct StatusCheck {
    std::string name;
    CheckState state;
};

struct BranchProtection {
    std::size_t required_reviews{2};
    std::unordered_set<std::string> required_checks;
    bool require_conversation_resolution{true};
    bool require_linear_history{true};
    bool allow_force_push{false};
    bool allow_deletion{false};
    bool allow_direct_push{false};
};

struct PullRequest {
    int number{};
    std::string title;
    std::string author;
    std::string source;
    std::string target;
    PRState state{PRState::Open};
    bool draft{false};
    bool mergeable{true};
    int base_behind_by{0};
    int unresolved_conversations{0};
    std::vector<Commit> commits;
    std::vector<Review> reviews;
    std::unordered_map<std::string, StatusCheck> checks;
};

struct Decision {
    bool eligible{false};
    std::vector<std::string> reasons;
};

class GovernanceEngine {
private:
    std::unordered_map<std::string, Person> members;
    std::unordered_map<std::string, BranchProtection> protections;

    bool eligibleReviewer(
        const std::string& username,
        const std::string& author
    ) const {
        if (username == author) {
            return false;
        }

        auto it = members.find(username);
        if (it == members.end()) {
            return false;
        }

        const auto& roles = it->second.roles;
        return roles.contains("reviewer") || roles.contains("maintainer");
    }

public:
    GovernanceEngine(
        std::vector<Person> people,
        std::unordered_map<std::string, BranchProtection> policies
    )
        : protections(std::move(policies)) {
        for (auto& person : people) {
            members.emplace(person.username, std::move(person));
        }
    }

    Decision evaluate(const PullRequest& pr) const {
        Decision decision;
        auto policy_it = protections.find(pr.target);

        if (pr.state != PRState::Open)
            decision.reasons.push_back("Pull request is not open.");

        if (pr.draft)
            decision.reasons.push_back("Draft pull request cannot be merged.");

        if (pr.commits.empty())
            decision.reasons.push_back("Pull request contains no commits.");

        if (!pr.mergeable)
            decision.reasons.push_back("Merge conflicts are present.");

        if (policy_it == protections.end()) {
            decision.reasons.push_back("Target branch is not protected.");
            return decision;
        }

        const auto& policy = policy_it->second;
        const std::string& head = pr.commits.back().sha;
        std::unordered_set<std::string> approvals;

        // Approvals are tied to the current head. A later commit therefore
        // invalidates earlier approvals in this governance model.
        for (const auto& review : pr.reviews) {
            if (
                review.state == ReviewState::Approved &&
                review.commit_sha == head &&
                eligibleReviewer(review.reviewer, pr.author)
            ) {
                approvals.insert(review.reviewer);
            }
        }

        if (approvals.size() < policy.required_reviews) {
            decision.reasons.push_back(
                "Required current approval count has not been reached."
            );
        }

        for (const auto& check_name : policy.required_checks) {
            auto check_it = pr.checks.find(check_name);
            if (
                check_it == pr.checks.end() ||
                check_it->second.state != CheckState::Passing
            ) {
                decision.reasons.push_back(
                    "Required check '" + check_name + "' is not passing."
                );
            }
        }

        if (
            policy.require_conversation_resolution &&
            pr.unresolved_conversations > 0
        ) {
            decision.reasons.push_back(
                "Unresolved review conversations remain."
            );
        }

        if (policy.require_linear_history && pr.base_behind_by > 0) {
            decision.reasons.push_back(
                "The source branch must synchronize with the base branch."
            );
        }

        decision.eligible = decision.reasons.empty();
        return decision;
    }
};

static void printDecision(
    const PullRequest& pr,
    const GovernanceEngine& engine
) {
    Decision decision = engine.evaluate(pr);

    std::cout
        << "PR #" << pr.number << ": " << pr.title << " -> "
        << (decision.eligible ? "MERGE ELIGIBLE" : "MERGE BLOCKED")
        << '\n';

    for (const auto& reason : decision.reasons) {
        std::cout << "  - " << reason << '\n';
    }
}

int main() {
    try {
        std::vector<Person> people{
            {"atul", {"developer"}},
            {"maya", {"reviewer"}},
            {"liam", {"maintainer"}},
            {"nora", {"reviewer"}}
        };

        BranchProtection main_policy;
        main_policy.required_reviews = 2;
        main_policy.required_checks = {"ci", "security"};
        main_policy.require_conversation_resolution = true;
        main_policy.require_linear_history = true;

        GovernanceEngine engine(
            std::move(people),
            {{"main", main_policy}}
        );

        PullRequest pr{
            142,
            "Add transaction idempotency protection",
            "atul",
            "feature/idempotency",
            "main"
        };

        pr.commits.push_back({
            "a1b2c3d",
            "Add idempotency validation",
            "atul"
        });

        pr.checks.emplace(
            "ci",
            StatusCheck{"ci", CheckState::Passing}
        );
        pr.checks.emplace(
            "security",
            StatusCheck{"security", CheckState::Passing}
        );

        pr.reviews.push_back({
            "maya",
            ReviewState::Approved,
            "a1b2c3d"
        });

        pr.reviews.push_back({
            "liam",
            ReviewState::Approved,
            "a1b2c3d"
        });

        printDecision(pr, engine);
        std::cout << '\n';

        // New commits invalidate approvals that reviewed the old head.
        pr.commits.push_back({
            "d4e5f6g",
            "Handle duplicate transaction requests",
            "atul"
        });

        printDecision(pr, engine);
        std::cout << '\n';

        pr.reviews.push_back({
            "maya",
            ReviewState::Approved,
            "d4e5f6g"
        });

        pr.reviews.push_back({
            "liam",
            ReviewState::Approved,
            "d4e5f6g"
        });

        pr.unresolved_conversations = 1;
        printDecision(pr, engine);
        std::cout << '\n';

        pr.unresolved_conversations = 0;
        printDecision(pr, engine);
    }
    catch (const std::exception& ex) {
        std::cerr << "Governance failure: " << ex.what() << '\n';
        return 1;
    }

    return 0;
}
