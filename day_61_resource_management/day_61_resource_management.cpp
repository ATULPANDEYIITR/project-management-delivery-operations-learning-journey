#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

enum class PullRequestState { Draft, Open, Closed, Merged };
enum class ReviewState { Commented, Approved, ChangesRequested, Dismissed };
enum class ResourceKind { Engineer, Reviewer, Automation };

struct Resource {
    std::string id;
    ResourceKind kind;
    double capacityHours;
    double hourlyCost;
    double allocatedHours{0.0};

    double utilization() const {
        return allocatedHours / capacityHours;
    }
};

class ResourceLedger {
private:
    std::map<std::string, Resource> resources;

public:
    void addResource(const Resource& resource) {
        if (resource.id.empty() || resource.capacityHours <= 0 ||
            resource.hourlyCost < 0) {
            throw std::invalid_argument("Invalid resource definition");
        }
        if (resources.contains(resource.id)) {
            throw std::invalid_argument("Duplicate resource");
        }
        resources.emplace(resource.id, resource);
    }

    void allocate(const std::string& id, double hours) {
        auto it = resources.find(id);
        if (it == resources.end()) {
            throw std::invalid_argument("Unknown resource: " + id);
        }
        if (hours <= 0) {
            throw std::invalid_argument("Allocation must be positive");
        }
        if (it->second.allocatedHours + hours > it->second.capacityHours) {
            throw std::runtime_error(
                "Resource capacity exceeded for " + id);
        }
        it->second.allocatedHours += hours;
    }

    double totalCost() const {
        double result = 0.0;
        for (const auto& [id, resource] : resources) {
            result += resource.allocatedHours * resource.hourlyCost;
        }
        return result;
    }

    void print() const {
        for (const auto& [id, resource] : resources) {
            std::cout << std::left << std::setw(14) << id
                      << " allocated=" << std::setw(6)
                      << resource.allocatedHours
                      << " capacity=" << std::setw(6)
                      << resource.capacityHours
                      << " utilization=" << std::fixed
                      << std::setprecision(1)
                      << resource.utilization() * 100.0 << "%\n";
        }
    }
};

struct Commit {
    std::string sha;
    std::string message;
    std::string author;
};

struct ReviewComment {
    std::string reviewer;
    std::string file;
    int line;
    std::string message;
    bool resolved{false};
};

struct Review {
    std::string reviewer;
    ReviewState state;
    std::string commitSha;
    std::vector<ReviewComment> comments;
};

struct StatusCheck {
    std::string name;
    bool passed;
};

struct BranchProtection {
    int requiredApprovals{1};
    std::set<std::string> requiredChecks;
    bool requireResolvedConversations{true};
    bool requireLinearHistory{true};
    bool allowDirectPush{false};
    bool allowForcePush{false};
    bool allowDeletion{false};
};

struct PullRequest {
    int number;
    std::string source;
    std::string target;
    std::string author;
    PullRequestState state;
    std::vector<Commit> commits;
    std::vector<Review> reviews;
    std::vector<StatusCheck> checks;
    std::string targetHead;
    bool baseSynchronized{true};
};

class GovernanceEngine {
private:
    std::map<std::string, std::vector<Commit>> branches;
    std::map<int, PullRequest> pullRequests;
    BranchProtection protection;
    int nextPr{1};

public:
    explicit GovernanceEngine(BranchProtection protection)
        : protection(std::move(protection)) {
        branches.emplace("main", std::vector<Commit>{});
    }

    void createBranch(const std::string& branch,
                      const std::string& base) {
        if (branches.contains(branch)) {
            throw std::invalid_argument("Branch already exists");
        }
        auto it = branches.find(base);
        if (it == branches.end()) {
            throw std::invalid_argument("Unknown base branch");
        }
        branches[branch] = it->second;
    }

    void addCommit(const std::string& branch,
                   const std::string& sha,
                   const std::string& message,
                   const std::string& author) {
        if (!branches.contains(branch)) {
            throw std::invalid_argument("Unknown branch");
        }
        if (sha.size() < 7 || message.empty() || author.empty()) {
            throw std::invalid_argument("Invalid commit");
        }
        branches[branch].push_back({sha, message, author});
    }

    int openPullRequest(const std::string& source,
                        const std::string& target,
                        const std::string& author) {
        if (!branches.contains(source) || !branches.contains(target)) {
            throw std::invalid_argument("Unknown source or target branch");
        }
        if (source == target) {
            throw std::invalid_argument("Source and target must differ");
        }
        if (branches[source].empty()) {
            throw std::invalid_argument("Pull request contains no commits");
        }

        const int number = nextPr++;
        PullRequest pr{
            number,
            source,
            target,
            author,
            PullRequestState::Open,
            branches[source],
            {},
            {},
            branches[target].empty() ? "" : branches[target].back().sha,
            true
        };

        pullRequests.emplace(number, std::move(pr));
        return number;
    }

    void addReview(int number,
                   const std::string& reviewer,
                   ReviewState state,
                   const std::string& commitSha,
                   std::vector<ReviewComment> comments = {}) {
        PullRequest& pr = pullRequests.at(number);

        if (pr.state != PullRequestState::Open &&
            pr.state != PullRequestState::Draft) {
            throw std::runtime_error("Pull request is inactive");
        }
        if (reviewer == pr.author) {
            throw std::runtime_error("Self-approval is prohibited");
        }

        pr.reviews.push_back(
            {reviewer, state, commitSha, std::move(comments)});
    }

    void resolveAllComments(int number) {
        PullRequest& pr = pullRequests.at(number);
        for (auto& review : pr.reviews) {
            for (auto& comment : review.comments) {
                comment.resolved = true;
            }
        }
    }

    void setCheck(int number,
                  const std::string& name,
                  bool passed) {
        PullRequest& pr = pullRequests.at(number);

        auto it = std::find_if(
            pr.checks.begin(),
            pr.checks.end(),
            [&](const StatusCheck& check) {
                return check.name == name;
            });

        if (it == pr.checks.end()) {
            pr.checks.push_back({name, passed});
        } else {
            it->passed = passed;
        }
    }

    std::pair<bool, std::vector<std::string>>
    evaluate(int number) const {
        const PullRequest& pr = pullRequests.at(number);
        std::vector<std::string> failures;

        if (pr.state != PullRequestState::Open) {
            failures.push_back("pull request is not open");
        }
        if (!pr.baseSynchronized) {
            failures.push_back("base branch is stale");
        }
        if (pr.commits.empty()) {
            failures.push_back("no commits exist");
        }

        std::set<std::string> approvals;
        const std::string latestSha = pr.commits.back().sha;

        for (const auto& review : pr.reviews) {
            if (review.state == ReviewState::Approved &&
                review.commitSha == latestSha &&
                pr.baseSynchronized) {
                approvals.insert(review.reviewer);
            }
        }

        if (static_cast<int>(approvals.size()) <
            protection.requiredApprovals) {
            failures.push_back("required approvals are missing");
        }

        for (const auto& required : protection.requiredChecks) {
            auto check = std::find_if(
                pr.checks.begin(),
                pr.checks.end(),
                [&](const StatusCheck& current) {
                    return current.name == required;
                });

            if (check == pr.checks.end() || !check->passed) {
                failures.push_back("required check failed: " + required);
            }
        }

        if (protection.requireResolvedConversations) {
            bool unresolved = false;
            for (const auto& review : pr.reviews) {
                for (const auto& comment : review.comments) {
                    if (!comment.resolved) {
                        unresolved = true;
                    }
                }
            }
            if (unresolved) {
                failures.push_back("unresolved conversations remain");
            }
        }

        if (protection.requireLinearHistory) {
            std::set<std::string> uniqueShas;
            for (const auto& commit : pr.commits) {
                uniqueShas.insert(commit.sha);
            }
            if (uniqueShas.size() != pr.commits.size()) {
                failures.push_back("non-linear duplicate commit history");
            }
        }

        return {failures.empty(), failures};
    }

    void merge(int number, const std::string& strategy) {
        if (strategy != "merge" &&
            strategy != "squash" &&
            strategy != "rebase") {
            throw std::invalid_argument("Unsupported merge strategy");
        }

        auto [eligible, failures] = evaluate(number);
        if (!eligible) {
            std::string message = "Merge blocked:";
            for (const auto& failure : failures) {
                message += " " + failure + ";";
            }
            throw std::runtime_error(message);
        }

        PullRequest& pr = pullRequests.at(number);
        auto& target = branches.at(pr.target);

        if (strategy == "squash") {
            target.push_back({
                "squash-" + std::to_string(number),
                "Squash merge PR #" + std::to_string(number),
                pr.author
            });
        } else {
            target.insert(target.end(),
                          pr.commits.begin(),
                          pr.commits.end());
        }

        pr.state = PullRequestState::Merged;
    }
};

int main() {
    try {
        ResourceLedger resources;
        resources.addResource(
            {"engineer-01", ResourceKind::Engineer, 32.0, 85.0});
        resources.addResource(
            {"reviewer-01", ResourceKind::Reviewer, 16.0, 110.0});
        resources.addResource(
            {"ci-01", ResourceKind::Automation, 20.0, 20.0});

        resources.allocate("engineer-01", 13.0);
        resources.allocate("reviewer-01", 4.0);
        resources.allocate("ci-01", 2.0);

        BranchProtection protection;
        protection.requiredApprovals = 1;
        protection.requiredChecks = {"unit-tests", "security-scan"};
        protection.requireResolvedConversations = true;
        protection.requireLinearHistory = true;

        GovernanceEngine repository(protection);

        repository.createBranch(
            "feature/resource-budget", "main");

        repository.addCommit(
            "feature/resource-budget",
            "abc1234",
            "Add resource budget model",
            "engineer-01");

        repository.addCommit(
            "feature/resource-budget",
            "def5678",
            "Enforce allocation limits",
            "engineer-01");

        int pr = repository.openPullRequest(
            "feature/resource-budget",
            "main",
            "engineer-01");

        repository.addReview(
            pr,
            "reviewer-01",
            ReviewState::ChangesRequested,
            "def5678",
            {
                {"reviewer-01", "resource.cpp", 81,
                 "Reject allocations beyond capacity.", false}
            });

        auto first = repository.evaluate(pr);
        std::cout << "Before resolution: "
                  << (first.first ? "eligible" : "blocked")
                  << '\n';

        repository.resolveAllComments(pr);

        repository.addReview(
            pr,
            "reviewer-01",
            ReviewState::Approved,
            "def5678");

        repository.setCheck(pr, "unit-tests", true);
        repository.setCheck(pr, "security-scan", true);

        auto second = repository.evaluate(pr);
        std::cout << "After policy checks: "
                  << (second.first ? "eligible" : "blocked")
                  << '\n';

        if (second.first) {
            repository.merge(pr, "squash");
            std::cout << "Pull request merged successfully.\n";
        }

        std::cout << "\nResource allocation:\n";
        resources.print();
        std::cout << "Project resource cost: $"
                  << std::fixed << std::setprecision(2)
                  << resources.totalCost() << '\n';

        try {
            resources.allocate("engineer-01", 25.0);
        } catch (const std::exception& ex) {
            std::cout << "Expected capacity failure: "
                      << ex.what() << '\n';
        }

    } catch (const std::exception& ex) {
        std::cerr << "Fatal error: " << ex.what() << '\n';
        return 1;
    }

    return 0;
}
