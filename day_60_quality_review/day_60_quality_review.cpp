#include <algorithm>
#include <cctype>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

enum class Role {
    Read,
    Write,
    Maintain,
    Admin
};

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
    Dismissed,
    Stale
};

enum class CheckState {
    Pending,
    Success,
    Failure
};

enum class MergeStrategy {
    Merge,
    Squash,
    Rebase
};

std::string toString(Role value) {
    switch (value) {
        case Role::Read: return "read";
        case Role::Write: return "write";
        case Role::Maintain: return "maintain";
        case Role::Admin: return "admin";
    }
    return "unknown";
}

std::string toString(ReviewState value) {
    switch (value) {
        case ReviewState::Commented: return "commented";
        case ReviewState::Approved: return "approved";
        case ReviewState::ChangesRequested: return "changes requested";
        case ReviewState::Dismissed: return "dismissed";
        case ReviewState::Stale: return "stale";
    }
    return "unknown";
}

std::string toString(PullRequestState value) {
    switch (value) {
        case PullRequestState::Draft: return "draft";
        case PullRequestState::Open: return "open";
        case PullRequestState::Closed: return "closed";
        case PullRequestState::Merged: return "merged";
    }
    return "unknown";
}

class GovernanceError : public std::runtime_error {
public:
    explicit GovernanceError(const std::string& message)
        : std::runtime_error(message) {}
};

struct Member {
    std::string username;
    Role role;
    bool active = true;
};

struct Commit {
    std::string id;
    std::string author;
    std::string message;
    std::vector<std::string> parents;
    std::set<std::string> changedPaths;
};

struct Review {
    int id;
    std::string reviewer;
    ReviewState state;
    std::string reviewedCommit;
    int sequence;
};

struct ReviewThread {
    int id;
    std::string author;
    std::string path;
    int line;
    std::string body;
    bool resolved = false;
};

struct StatusCheck {
    std::string context;
    std::string commitId;
    CheckState state;
};

struct Branch {
    std::string name;
    std::string head;
    bool deleted = false;
};

struct BranchProtection {
    int requiredApprovals = 1;
    std::set<std::string> requiredChecks;
    bool dismissStaleApprovals = true;
    bool requireResolvedThreads = true;
    bool requireLinearHistory = false;
    bool allowDirectPush = false;
    bool allowForcePush = false;
    bool allowDeletion = false;
    bool administratorsEnforced = true;
    std::set<Role> bypassRoles;
};

struct PullRequest {
    int id;
    std::string title;
    std::string author;
    std::string sourceBranch;
    std::string targetBranch;
    std::string baseCommit;
    std::string headCommit;
    PullRequestState state;
    MergeStrategy strategy;
    bool conflicted = false;
    std::set<std::string> changedPaths;
    std::vector<Review> reviews;
    std::vector<ReviewThread> threads;
    std::map<std::pair<std::string, std::string>, StatusCheck> checks;
    std::string mergedCommit;
};

struct EligibilityReport {
    bool eligible = false;
    std::vector<std::string> blockers;
};

class RepositoryGovernance {
private:
    std::string name_;
    std::map<std::string, Member> members_;
    std::map<std::string, Branch> branches_;
    std::map<std::string, Commit> commits_;
    std::map<std::string, BranchProtection> policies_;
    std::map<int, PullRequest> pullRequests_;
    int commitSequence_ = 0;
    int pullRequestSequence_ = 0;
    int reviewSequence_ = 0;
    int threadSequence_ = 0;

    static std::string normalizePath(const std::string& path) {
        if (path.empty() || path.front() == '/') {
            throw GovernanceError("Invalid repository path.");
        }

        std::string normalized = path;
        std::replace(normalized.begin(), normalized.end(), '\\', '/');

        std::size_t start = 0;
        while (start <= normalized.size()) {
            const std::size_t end = normalized.find('/', start);
            const std::string part = normalized.substr(
                start,
                end == std::string::npos ? std::string::npos : end - start
            );
            if (part == ".." || part.empty()) {
                throw GovernanceError("Unsafe or malformed repository path.");
            }
            if (end == std::string::npos) break;
            start = end + 1;
        }
        return normalized;
    }

    const Member& member(const std::string& username) const {
        const auto it = members_.find(username);
        if (it == members_.end() || !it->second.active) {
            throw GovernanceError("Unknown or inactive repository member: " + username);
        }
        return it->second;
    }

    PullRequest& pullRequest(int id) {
        auto it = pullRequests_.find(id);
        if (it == pullRequests_.end()) {
            throw GovernanceError("Pull Request does not exist.");
        }
        return it->second;
    }

    const PullRequest& pullRequest(int id) const {
        const auto it = pullRequests_.find(id);
        if (it == pullRequests_.end()) {
            throw GovernanceError("Pull Request does not exist.");
        }
        return it->second;
    }

    Commit createCommit(
        const std::string& author,
        const std::string& message,
        std::vector<std::string> parents,
        const std::set<std::string>& paths
    ) {
        if (message.empty()) {
            throw GovernanceError("Commit message cannot be empty.");
        }
        for (const auto& parent : parents) {
            if (commits_.find(parent) == commits_.end()) {
                throw GovernanceError("Commit references an unknown parent.");
            }
        }

        Commit commit;
        commit.id = "c" + std::to_string(++commitSequence_);
        commit.author = author;
        commit.message = message;
        commit.parents = std::move(parents);

        for (const auto& path : paths) {
            commit.changedPaths.insert(normalizePath(path));
        }

        commits_.emplace(commit.id, commit);
        return commit;
    }

    std::set<std::string> pathsSince(
        const std::string& head,
        const std::string& base
    ) const {
        std::set<std::string> paths;
        std::string cursor = head;
        std::set<std::string> visited;

        while (cursor != base) {
            if (visited.count(cursor) || commits_.find(cursor) == commits_.end()) {
                throw GovernanceError("Base commit is not an ancestor of the branch.");
            }

            visited.insert(cursor);
            const auto& commit = commits_.at(cursor);
            paths.insert(commit.changedPaths.begin(), commit.changedPaths.end());

            if (commit.parents.empty()) {
                throw GovernanceError("Base commit is not an ancestor of the branch.");
            }
            cursor = commit.parents.front();
        }

        return paths;
    }

    bool hasBypass(const BranchProtection& policy, Role actorRole) const {
        if (policy.bypassRoles.count(actorRole) > 0) return true;
        return actorRole == Role::Admin && !policy.administratorsEnforced;
    }

public:
    explicit RepositoryGovernance(
        std::string name,
        const std::vector<Member>& members
    ) : name_(std::move(name)) {
        if (name_.empty()) {
            throw GovernanceError("Repository name cannot be empty.");
        }

        for (const auto& item : members) {
            if (item.username.empty() || members_.count(item.username)) {
                throw GovernanceError("Member usernames must be unique and non-empty.");
            }
            members_.emplace(item.username, item);
        }

        const Commit root = createCommit(
            "system",
            "Initial repository commit",
            {},
            {}
        );
        branches_.emplace("main", Branch{"main", root.id, false});
    }

    void protectBranch(
        const std::string& branchName,
        const BranchProtection& policy
    ) {
        if (branches_.find(branchName) == branches_.end()) {
            throw GovernanceError("Cannot protect an unknown branch.");
        }
        if (policy.requiredApprovals < 0) {
            throw GovernanceError("Required approvals cannot be negative.");
        }

        policies_[branchName] = policy;
    }

    void createBranch(const std::string& name, const std::string& source = "main") {
        const auto sourceIt = branches_.find(source);
        if (name.empty() || branches_.count(name) ||
            sourceIt == branches_.end() || sourceIt->second.deleted) {
            throw GovernanceError("Invalid branch creation request.");
        }

        branches_.emplace(name, Branch{name, sourceIt->second.head, false});
    }

    void push(
        const std::string& branchName,
        const std::string& author,
        const std::string& message,
        const std::set<std::string>& paths,
        bool force = false
    ) {
        const Member& actor = member(author);
        auto branchIt = branches_.find(branchName);

        if (branchIt == branches_.end() || branchIt->second.deleted) {
            throw GovernanceError("Branch does not exist.");
        }
        if (actor.role == Role::Read) {
            throw GovernanceError("Read-only members cannot push.");
        }

        const auto policyIt = policies_.find(branchName);
        if (policyIt != policies_.end()) {
            const auto& policy = policyIt->second;
            const bool bypass = hasBypass(policy, actor.role);

            if (!policy.allowDirectPush && !bypass) {
                throw GovernanceError("Protected branch rejects direct pushes.");
            }
            if (force && !policy.allowForcePush) {
                throw GovernanceError("Protected branch rejects force pushes.");
            }
        }

        const std::vector<std::string> parents =
            force ? std::vector<std::string>{}
                  : std::vector<std::string>{branchIt->second.head};

        const Commit commit = createCommit(author, message, parents, paths);
        branchIt->second.head = commit.id;
    }

    int openPullRequest(
        const std::string& title,
        const std::string& author,
        const std::string& source,
        const std::string& target = "main",
        bool draft = false,
        MergeStrategy strategy = MergeStrategy::Squash
    ) {
        member(author);
        const auto sourceIt = branches_.find(source);
        const auto targetIt = branches_.find(target);

        if (title.empty() || source == target ||
            sourceIt == branches_.end() || targetIt == branches_.end() ||
            sourceIt->second.deleted || targetIt->second.deleted) {
            throw GovernanceError("Invalid Pull Request configuration.");
        }
        if (sourceIt->second.head == targetIt->second.head) {
            throw GovernanceError("There are no proposed changes.");
        }

        PullRequest pr;
        pr.id = ++pullRequestSequence_;
        pr.title = title;
        pr.author = author;
        pr.sourceBranch = source;
        pr.targetBranch = target;
        pr.baseCommit = targetIt->second.head;
        pr.headCommit = sourceIt->second.head;
        pr.state = draft ? PullRequestState::Draft : PullRequestState::Open;
        pr.strategy = strategy;
        pr.changedPaths = pathsSince(pr.headCommit, pr.baseCommit);

        pullRequests_.emplace(pr.id, pr);
        return pr.id;
    }

    void markReady(int id, const std::string& actor) {
        member(actor);
        PullRequest& pr = pullRequest(id);
        if (pr.state != PullRequestState::Draft) {
            throw GovernanceError("Only draft Pull Requests can be marked ready.");
        }
        pr.state = PullRequestState::Open;
    }

    void submitReview(
        int id,
        const std::string& reviewer,
        ReviewState state
    ) {
        PullRequest& pr = pullRequest(id);
        const Member& reviewerMember = member(reviewer);

        if (pr.state != PullRequestState::Open ||
            reviewer == pr.author ||
            reviewerMember.role == Role::Read) {
            throw GovernanceError("Reviewer is not eligible.");
        }
        if (state != ReviewState::Commented &&
            state != ReviewState::Approved &&
            state != ReviewState::ChangesRequested) {
            throw GovernanceError("Invalid submitted review state.");
        }

        pr.reviews.push_back(Review{
            ++reviewSequence_,
            reviewer,
            state,
            pr.headCommit,
            reviewSequence_
        });
    }

    void dismissReview(int id, int reviewId, const std::string& actor) {
        PullRequest& pr = pullRequest(id);
        const Role role = member(actor).role;

        if (role != Role::Maintain && role != Role::Admin) {
            throw GovernanceError("Only maintainers or administrators can dismiss reviews.");
        }

        for (auto& review : pr.reviews) {
            if (review.id == reviewId) {
                review.state = ReviewState::Dismissed;
                return;
            }
        }
        throw GovernanceError("Review does not exist.");
    }

    int addDiscussion(
        int id,
        const std::string& author,
        const std::string& path,
        int line,
        const std::string& body
    ) {
        PullRequest& pr = pullRequest(id);
        if (pr.state != PullRequestState::Open ||
            member(author).role == Role::Read) {
            throw GovernanceError("Member cannot create a discussion.");
        }

        const std::string normalized = normalizePath(path);
        if (line < 1 || body.empty() ||
            pr.changedPaths.count(normalized) == 0) {
            throw GovernanceError("Invalid inline discussion.");
        }

        const int idValue = ++threadSequence_;
        pr.threads.push_back(
            ReviewThread{idValue, author, normalized, line, body, false}
        );
        return idValue;
    }

    void resolveDiscussion(int id, int threadId, const std::string& actor) {
        PullRequest& pr = pullRequest(id);
        if (member(actor).role == Role::Read) {
            throw GovernanceError("Read-only members cannot resolve discussions.");
        }

        for (auto& thread : pr.threads) {
            if (thread.id == threadId) {
                thread.resolved = true;
                return;
            }
        }
        throw GovernanceError("Discussion does not exist.");
    }

    void recordCheck(
        int id,
        const std::string& context,
        CheckState state,
        const std::string& commitId = ""
    ) {
        PullRequest& pr = pullRequest(id);
        if (context.empty()) {
            throw GovernanceError("Status-check context cannot be empty.");
        }
        if (pr.state != PullRequestState::Open &&
            pr.state != PullRequestState::Draft) {
            throw GovernanceError("Pull Request is not accepting check updates.");
        }

        const std::string checkedCommit =
            commitId.empty() ? pr.headCommit : commitId;

        if (commits_.find(checkedCommit) == commits_.end()) {
            throw GovernanceError("Status check references an unknown commit.");
        }

        pr.checks[{context, checkedCommit}] =
            StatusCheck{context, checkedCommit, state};
    }

    EligibilityReport evaluateMerge(
        int id,
        const std::string& actor
    ) const {
        const PullRequest& pr = pullRequest(id);
        const Role actorRole = member(actor).role;

        BranchProtection defaultPolicy;
        defaultPolicy.requiredApprovals = 0;
        defaultPolicy.requiredChecks.clear();
        defaultPolicy.requireResolvedThreads = false;

        const auto policyIt = policies_.find(pr.targetBranch);
        const BranchProtection& policy =
            policyIt == policies_.end() ? defaultPolicy : policyIt->second;

        EligibilityReport report;

        const auto sourceIt = branches_.find(pr.sourceBranch);
        const auto targetIt = branches_.find(pr.targetBranch);

        if (pr.state != PullRequestState::Open) {
            report.blockers.push_back("Pull Request is not open.");
        }
        if (sourceIt == branches_.end() || sourceIt->second.deleted ||
            targetIt == branches_.end() || targetIt->second.deleted) {
            report.blockers.push_back("Source or target branch is unavailable.");
            return report;
        }
        if (sourceIt->second.head != pr.headCommit) {
            report.blockers.push_back("Source branch has unreviewed commits.");
        }
        if (targetIt->second.head != pr.baseCommit) {
            report.blockers.push_back("Target branch has advanced.");
        }
        if (pr.conflicted) {
            report.blockers.push_back("Merge conflicts remain unresolved.");
        }

        const bool bypass = hasBypass(policy, actorRole);
        if (!bypass) {
            for (const auto& context : policy.requiredChecks) {
                const auto check = pr.checks.find({context, pr.headCommit});
                if (check == pr.checks.end() ||
                    check->second.state != CheckState::Success) {
                    report.blockers.push_back(
                        "Required check has not succeeded: " + context
                    );
                }
            }

            // The newest decision from each reviewer supersedes earlier decisions.
            std::map<std::string, Review> latestReviews;
            for (const auto& review : pr.reviews) {
                const auto it = latestReviews.find(review.reviewer);
                if (it == latestReviews.end() ||
                    review.sequence > it->second.sequence) {
                    latestReviews[review.reviewer] = review;
                }
            }

            int approvals = 0;
            for (const auto& entry : latestReviews) {
                const Review& review = entry.second;
                const Member& reviewer = member(review.reviewer);

                if (review.reviewer == pr.author || reviewer.role == Role::Read) {
                    continue;
                }
                if (policy.dismissStaleApprovals &&
                    review.reviewedCommit != pr.headCommit) {
                    continue;
                }

                if (review.state == ReviewState::ChangesRequested) {
                    report.blockers.push_back(
                        review.reviewer + " has requested changes."
                    );
                } else if (review.state == ReviewState::Approved) {
                    ++approvals;
                }
            }

            if (approvals < policy.requiredApprovals) {
                report.blockers.push_back(
                    "Insufficient approvals: " +
                    std::to_string(approvals) + "/" +
                    std::to_string(policy.requiredApprovals)
                );
            }

            if (policy.requireResolvedThreads) {
                const auto unresolved = std::count_if(
                    pr.threads.begin(),
                    pr.threads.end(),
                    [](const ReviewThread& thread) {
                        return !thread.resolved;
                    }
                );
                if (unresolved > 0) {
                    report.blockers.push_back(
                        std::to_string(unresolved) +
                        " review discussion(s) remain unresolved."
                    );
                }
            }

            if (policy.requireLinearHistory &&
                pr.strategy == MergeStrategy::Merge) {
                report.blockers.push_back(
                    "Selected merge strategy violates linear-history policy."
                );
            }
        }

        report.eligible = report.blockers.empty();
        return report;
    }

    std::string merge(int id, const std::string& actor) {
        PullRequest& pr = pullRequest(id);
        const EligibilityReport report = evaluateMerge(id, actor);

        if (!report.eligible) {
            std::string message = "Merge blocked:";
            for (const auto& blocker : report.blockers) {
                message += " [" + blocker + "]";
            }
            throw GovernanceError(message);
        }

        Branch& target = branches_.at(pr.targetBranch);
        const Branch& source = branches_.at(pr.sourceBranch);
        std::vector<std::string> parents;
        std::string message;

        if (pr.strategy == MergeStrategy::Merge) {
            parents = {target.head, source.head};
            message = "Merge Pull Request #" + std::to_string(id);
        } else {
            parents = {target.head};
            message = pr.strategy == MergeStrategy::Squash
                ? "Squash Pull Request #" + std::to_string(id)
                : "Rebase Pull Request #" + std::to_string(id);
        }

        const Commit commit = createCommit(
            actor,
            message,
            parents,
            pr.changedPaths
        );

        target.head = commit.id;
        pr.state = PullRequestState::Merged;
        pr.mergedCommit = commit.id;
        return commit.id;
    }

    void close(int id, const std::string& actor) {
        PullRequest& pr = pullRequest(id);
        const Member& memberData = member(actor);

        if (pr.state != PullRequestState::Open &&
            pr.state != PullRequestState::Draft) {
            throw GovernanceError("Pull Request cannot be closed from this state.");
        }
        if (actor != pr.author && memberData.role == Role::Read) {
            throw GovernanceError("Actor cannot close this Pull Request.");
        }
        pr.state = PullRequestState::Closed;
    }

    void reopen(int id, const std::string& actor) {
        PullRequest& pr = pullRequest(id);
        const Member& memberData = member(actor);

        if (pr.state != PullRequestState::Closed) {
            throw GovernanceError("Only closed Pull Requests can be reopened.");
        }
        if (actor != pr.author && memberData.role == Role::Read) {
            throw GovernanceError("Actor cannot reopen this Pull Request.");
        }
        pr.state = PullRequestState::Open;
    }
};

int main() {
    try {
        RepositoryGovernance repository(
            "quality-review-engine",
            {
                {"developer", Role::Write, true},
                {"reviewer", Role::Maintain, true},
                {"administrator", Role::Admin, true}
            }
        );

        BranchProtection policy;
        policy.requiredApprovals = 1;
        policy.requiredChecks = {"unit-tests", "security-scan"};
        policy.dismissStaleApprovals = true;
        policy.requireResolvedThreads = true;
        policy.requireLinearHistory = true;
        policy.allowDirectPush = false;
        policy.allowForcePush = false;
        policy.allowDeletion = false;
        policy.administratorsEnforced = true;

        repository.protectBranch("main", policy);
        repository.createBranch("feature/quality-gates");

        repository.push(
            "feature/quality-gates",
            "developer",
            "Implement quality review validation",
            {"src/review.cpp", "tests/review_test.cpp"}
        );

        const int prId = repository.openPullRequest(
            "Add repository quality gates",
            "developer",
            "feature/quality-gates",
            "main",
            false,
            MergeStrategy::Squash
        );

        repository.submitReview(prId, "reviewer", ReviewState::Approved);

        const int threadId = repository.addDiscussion(
            prId,
            "reviewer",
            "src/review.cpp",
            21,
            "The policy handles reviewer eligibility and stale decisions."
        );
        repository.resolveDiscussion(prId, threadId, "developer");

        repository.recordCheck(prId, "unit-tests", CheckState::Success);
        repository.recordCheck(prId, "security-scan", CheckState::Success);

        const EligibilityReport report =
            repository.evaluateMerge(prId, "developer");

        std::cout << "Pull Request #" << prId << '\n';
        std::cout << "Merge eligible: "
                  << (report.eligible ? "yes" : "no") << '\n';

        for (const auto& blocker : report.blockers) {
            std::cout << "Blocker: " << blocker << '\n';
        }

        if (report.eligible) {
            const std::string mergeCommit =
                repository.merge(prId, "developer");
            std::cout << "Merged with commit: " << mergeCommit << '\n';
        }

        try {
            repository.push(
                "main",
                "developer",
                "Attempt direct protected-branch push",
                {"src/unreviewed.cpp"}
            );
        } catch (const GovernanceError& error) {
            std::cout << "Expected policy rejection: "
                      << error.what() << '\n';
        }
    } catch (const std::exception& error) {
        std::cerr << "Governance failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
