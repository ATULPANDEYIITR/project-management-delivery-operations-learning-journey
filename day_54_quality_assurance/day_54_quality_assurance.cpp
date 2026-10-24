#include <algorithm>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

enum class PRState { Open, Merged, Closed };
enum class ReviewState { Commented, Approved, ChangesRequested, Dismissed };
enum class CheckState { Pending, Passed, Failed };
enum class MergeStrategy { MergeCommit, Squash, Rebase };

struct Commit {
    std::string id;
    std::string message;
    std::string author;
    std::vector<std::string> parents;
};

struct Branch {
    std::string name;
    std::vector<Commit> commits;
    bool protectedBranch = false;

    std::string head() const {
        return commits.empty() ? "" : commits.back().id;
    }
};

struct Review {
    std::string reviewer;
    ReviewState state;
    std::string commitId;
    std::vector<std::string> comments;
};

struct StatusCheck {
    std::string name;
    CheckState state;
    std::string commitId;
};

struct ProtectionPolicy {
    std::size_t requiredApprovals = 2;
    std::set<std::string> requiredChecks{"unit-tests", "security-scan"};
    bool requireResolvedConversations = true;
    bool requireLinearHistory = true;
    bool allowDirectPush = false;
    bool allowForcePush = false;
    bool allowDeletion = false;
    bool allowAdminBypass = false;
};

class PullRequest {
public:
    int number;
    std::string author;
    Branch& source;
    Branch& target;
    const ProtectionPolicy& policy;
    std::set<std::string> eligibleReviewers;
    PRState state = PRState::Open;
    bool draft = false;
    std::vector<Review> reviews;
    std::map<std::string, StatusCheck> checks;
    std::map<std::string, bool> conversations;
    std::string baseHead;
    std::string mergeId;

    PullRequest(
        int prNumber,
        std::string prAuthor,
        Branch& sourceBranch,
        Branch& targetBranch,
        const ProtectionPolicy& branchPolicy,
        std::set<std::string> reviewers,
        bool isDraft = false
    )
        : number(prNumber),
          author(std::move(prAuthor)),
          source(sourceBranch),
          target(targetBranch),
          policy(branchPolicy),
          eligibleReviewers(std::move(reviewers)),
          draft(isDraft),
          baseHead(target.head()) {
        if (number <= 0 || author.empty()) {
            throw std::invalid_argument("Invalid pull request identity.");
        }
        if (source.name == target.name) {
            throw std::invalid_argument("Source and target must differ.");
        }
        if (eligibleReviewers.count(author)) {
            throw std::invalid_argument("Author cannot be an eligible reviewer.");
        }
    }

    void requireOpen() const {
        if (state != PRState::Open) {
            throw std::logic_error("Operation requires an open PR.");
        }
    }

    void addCommit(const Commit& commit) {
        requireOpen();
        if (commit.author != author || commit.id.empty()) {
            throw std::invalid_argument("Invalid source commit.");
        }
        const auto duplicate = std::find_if(
            source.commits.begin(), source.commits.end(),
            [&](const Commit& existing) { return existing.id == commit.id; }
        );
        if (duplicate != source.commits.end()) {
            throw std::invalid_argument("Duplicate source commit ID.");
        }
        source.commits.push_back(commit);
    }

    void synchronizeBase() {
        requireOpen();
        baseHead = target.head();
    }

    void submitReview(const Review& review) {
        requireOpen();
        if (draft) throw std::logic_error("Draft PR cannot be reviewed.");
        if (review.reviewer == author ||
            !eligibleReviewers.count(review.reviewer)) {
            throw std::invalid_argument("Reviewer is not eligible.");
        }
        if (review.commitId != source.head()) {
            throw std::invalid_argument("Review does not reference current HEAD.");
        }
        if (review.state == ReviewState::Dismissed) {
            throw std::invalid_argument("Cannot submit a dismissed review.");
        }
        reviews.push_back(review);
    }

    void setCheck(const std::string& name, CheckState stateValue) {
        requireOpen();
        if (name.empty()) throw std::invalid_argument("Check name is required.");
        checks[name] = StatusCheck{name, stateValue, source.head()};
    }

    void openConversation(const std::string& id) {
        requireOpen();
        if (id.empty()) throw std::invalid_argument("Conversation ID is required.");
        conversations[id] = false;
    }

    void resolveConversation(const std::string& id) {
        requireOpen();
        auto it = conversations.find(id);
        if (it == conversations.end() || it->second) {
            throw std::invalid_argument("Conversation is missing or resolved.");
        }
        it->second = true;
    }

    void dismissReview(const std::string& reviewer) {
        requireOpen();
        for (auto it = reviews.rbegin(); it != reviews.rend(); ++it) {
            if (it->reviewer == reviewer && it->state != ReviewState::Dismissed) {
                it->state = ReviewState::Dismissed;
                return;
            }
        }
        throw std::invalid_argument("No active review exists.");
    }

    std::map<std::string, Review> latestReviews() const {
        std::map<std::string, Review> latest;
        for (const auto& review : reviews) latest[review.reviewer] = review;
        return latest;
    }

    std::vector<std::string> evaluateMerge() const {
        std::vector<std::string> blockers;

        if (state != PRState::Open) {
            blockers.push_back("PR is not open.");
            return blockers;
        }
        if (draft) blockers.push_back("PR is a draft.");
        if (source.commits.empty()) blockers.push_back("Source branch is empty.");
        if (baseHead != target.head()) {
            blockers.push_back("Target changed; synchronize the base branch.");
        }

        std::size_t approvals = 0;
        const auto latest = latestReviews();

        for (const auto& entry : latest) {
            const Review& review = entry.second;
            if (review.commitId != source.head()) continue;

            if (review.state == ReviewState::Approved) {
                ++approvals;
            } else if (review.state == ReviewState::ChangesRequested) {
                blockers.push_back(entry.first + " requested changes.");
            }
        }

        if (approvals < policy.requiredApprovals) {
            blockers.push_back(
                "Insufficient current approvals: " + std::to_string(approvals)
            );
        }

        for (const auto& name : policy.requiredChecks) {
            const auto it = checks.find(name);
            if (it == checks.end() ||
                it->second.commitId != source.head() ||
                it->second.state != CheckState::Passed) {
                blockers.push_back("Required check failed or is stale: " + name);
            }
        }

        if (policy.requireResolvedConversations) {
            for (const auto& conversation : conversations) {
                if (!conversation.second) {
                    blockers.push_back(
                        "Unresolved conversation: " + conversation.first
                    );
                }
            }
        }

        if (policy.requireLinearHistory) {
            std::set<std::string> ids;
            for (const auto& commit : source.commits) {
                if (!ids.insert(commit.id).second) {
                    blockers.push_back("Duplicate commit in source history.");
                    break;
                }
                if (commit.parents.size() > 1) {
                    blockers.push_back("Merge commit violates linear-history policy.");
                    break;
                }
            }
        }

        return blockers;
    }

    Commit merge(const std::string& actor, MergeStrategy strategy) {
        requireOpen();
        if (!eligibleReviewers.count(actor) && actor != author) {
            throw std::invalid_argument("Actor lacks merge permission.");
        }

        const auto blockers = evaluateMerge();
        if (!blockers.empty()) {
            std::string message = "Merge blocked:";
            for (const auto& blocker : blockers) message += "\n- " + blocker;
            throw std::runtime_error(message);
        }

        const std::string id = "merge-" + std::to_string(number);
        std::vector<std::string> parents;

        if (strategy == MergeStrategy::MergeCommit) {
            if (!target.head().empty()) parents.push_back(target.head());
            if (!source.head().empty()) parents.push_back(source.head());
        } else if (strategy == MergeStrategy::Squash) {
            if (!target.head().empty()) parents.push_back(target.head());
        } else {
            // Rebase is represented as a single linear target commit in this model.
            if (!target.head().empty()) parents.push_back(target.head());
        }

        Commit result{
            id,
            "Integrate pull request #" + std::to_string(number),
            actor,
            parents
        };

        target.commits.push_back(result);
        state = PRState::Merged;
        mergeId = id;
        return result;
    }

    void close() {
        requireOpen();
        state = PRState::Closed;
    }

    void reopen() {
        if (state != PRState::Closed) {
            throw std::logic_error("Only a closed PR can be reopened.");
        }
        state = PRState::Open;
        baseHead = target.head();
    }
};

void directPush(
    Branch& branch,
    const Commit& commit,
    const ProtectionPolicy& policy,
    bool actorIsAdmin = false
) {
    if (branch.protectedBranch && !policy.allowDirectPush &&
        !(actorIsAdmin && policy.allowAdminBypass)) {
        throw std::runtime_error("Branch protection rejects direct push.");
    }
    if (commit.id.empty()) throw std::invalid_argument("Commit ID is required.");
    branch.commits.push_back(commit);
}

int main() {
    try {
        ProtectionPolicy policy;
        Branch main{
            "main",
            {{"c100", "Initial release", "maintainer", {}}},
            true
        };
        Branch feature{"feature/governance", {}, false};

        PullRequest pr(
            84,
            "developer",
            feature,
            main,
            policy,
            {"reviewer-a", "reviewer-b", "maintainer"},
            true
        );

        pr.draft = false;
        pr.addCommit({
            "c101",
            "Add request validation",
            "developer",
            {}
        });

        pr.openConversation("thread-1");
        pr.submitReview({
            "reviewer-a", ReviewState::Approved, "c101", {}
        });
        pr.submitReview({
            "reviewer-b", ReviewState::Approved, "c101", {}
        });
        pr.setCheck("unit-tests", CheckState::Passed);
        pr.setCheck("security-scan", CheckState::Passed);

        std::cout << "Initial blockers:\n";
        for (const auto& blocker : pr.evaluateMerge()) {
            std::cout << "- " << blocker << '\n';
        }

        pr.resolveConversation("thread-1");
        pr.addCommit({
            "c102",
            "Reject invalid identifiers",
            "developer",
            {"c101"}
        });

        std::cout << "\nAfter new commit:\n";
        for (const auto& blocker : pr.evaluateMerge()) {
            std::cout << "- " << blocker << '\n';
        }

        pr.submitReview({
            "reviewer-a", ReviewState::Approved, "c102", {}
        });
        pr.submitReview({
            "reviewer-b", ReviewState::Approved, "c102", {}
        });
        pr.setCheck("unit-tests", CheckState::Passed);
        pr.setCheck("security-scan", CheckState::Passed);

        const auto finalBlockers = pr.evaluateMerge();
        if (!finalBlockers.empty()) {
            throw std::runtime_error("Unexpected merge blockers.");
        }

        const Commit merged = pr.merge("maintainer", MergeStrategy::Squash);
        std::cout << "\nMerged as " << merged.id
                  << ", target HEAD " << main.head() << '\n';

        try {
            directPush(
                main,
                {"c103", "Unreviewed change", "developer", {}},
                policy
            );
        } catch (const std::exception& error) {
            std::cout << "Protection control: " << error.what() << '\n';
        }

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Governance failure: " << error.what() << '\n';
        return 1;
    }
}
