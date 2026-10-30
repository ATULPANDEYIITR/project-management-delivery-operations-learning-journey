import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

/**
 * Enterprise repository-governance model.
 * Compatible with Java 17 and requires no third-party dependencies.
 */
public class RepositoryQualityGovernance {

    enum Role {
        READ, WRITE, MAINTAIN, ADMIN
    }

    enum PullRequestState {
        DRAFT, OPEN, CLOSED, MERGED
    }

    enum ReviewDecision {
        COMMENTED, APPROVED, CHANGES_REQUESTED, DISMISSED, STALE
    }

    enum CheckState {
        PENDING, SUCCESS, FAILURE
    }

    enum MergeStrategy {
        MERGE, SQUASH, REBASE
    }

    static final class GovernanceException extends RuntimeException {
        GovernanceException(String message) {
            super(message);
        }
    }

    record RepositoryMember(String username, Role role, boolean active) {
        RepositoryMember {
            Objects.requireNonNull(username);
            Objects.requireNonNull(role);
            if (username.isBlank()) {
                throw new GovernanceException("Username cannot be empty.");
            }
        }

        boolean canReview() {
            return active && role != Role.READ;
        }

        boolean canAdminister() {
            return active && (role == Role.MAINTAIN || role == Role.ADMIN);
        }
    }

    record StatusCheck(String context, String commitId, CheckState state) {
        StatusCheck {
            Objects.requireNonNull(context);
            Objects.requireNonNull(commitId);
            Objects.requireNonNull(state);
            if (context.isBlank() || commitId.isBlank()) {
                throw new GovernanceException("Check context and commit are required.");
            }
        }
    }

    record Review(
        int id,
        String reviewer,
        ReviewDecision decision,
        String reviewedCommit,
        long sequence
    ) {
        Review {
            Objects.requireNonNull(reviewer);
            Objects.requireNonNull(decision);
            Objects.requireNonNull(reviewedCommit);
        }
    }

    record Discussion(
        int id,
        String author,
        String path,
        int line,
        String body,
        boolean resolved
    ) {
        Discussion {
            Objects.requireNonNull(author);
            Objects.requireNonNull(path);
            Objects.requireNonNull(body);
            if (line < 1 || body.isBlank()) {
                throw new GovernanceException("Invalid review discussion.");
            }
        }

        Discussion resolve() {
            return new Discussion(id, author, path, line, body, true);
        }
    }

    record ApprovalRequirement(Role reviewerRole, int minimumCount) {
        ApprovalRequirement {
            Objects.requireNonNull(reviewerRole);
            if (reviewerRole == Role.READ || minimumCount < 0) {
                throw new GovernanceException("Invalid role-specific approval requirement.");
            }
        }
    }

    record BranchPolicy(
        int requiredApprovals,
        Set<String> requiredChecks,
        List<ApprovalRequirement> roleRequirements,
        boolean dismissStaleApprovals,
        boolean requireResolvedDiscussions,
        boolean requireLinearHistory,
        boolean allowDirectPush,
        boolean allowForcePush,
        boolean allowDeletion,
        boolean administratorsEnforced,
        Set<Role> bypassRoles
    ) {
        BranchPolicy {
            if (requiredApprovals < 0) {
                throw new GovernanceException("Required approvals cannot be negative.");
            }
            requiredChecks = Set.copyOf(requiredChecks);
            roleRequirements = List.copyOf(roleRequirements);
            bypassRoles = Set.copyOf(bypassRoles);
            if (requiredChecks.stream().anyMatch(String::isBlank)) {
                throw new GovernanceException("Required check names cannot be blank.");
            }
        }

        boolean permitsBypass(Role actorRole) {
            return bypassRoles.contains(actorRole)
                || (actorRole == Role.ADMIN && !administratorsEnforced);
        }
    }

    record Branch(String name, String headCommit, boolean deleted) {
        Branch {
            Objects.requireNonNull(name);
            Objects.requireNonNull(headCommit);
            if (name.isBlank() || headCommit.isBlank()) {
                throw new GovernanceException("Branch name and head are required.");
            }
        }

        Branch withHead(String newHead) {
            return new Branch(name, newHead, deleted);
        }
    }

    static final class PullRequest {
        private final int id;
        private final String title;
        private final String author;
        private final String sourceBranch;
        private final String targetBranch;
        private final MergeStrategy strategy;
        private final List<Review> reviews = new ArrayList<>();
        private final Map<String, StatusCheck> checks = new HashMap<>();
        private final Map<Integer, Discussion> discussions = new LinkedHashMap<>();

        private String baseCommit;
        private String headCommit;
        private PullRequestState state;
        private boolean conflicted;
        private Set<String> changedPaths;
        private String mergedCommit;
        private int nextDiscussionId = 1;

        PullRequest(
            int id,
            String title,
            String author,
            String sourceBranch,
            String targetBranch,
            String baseCommit,
            String headCommit,
            boolean draft,
            MergeStrategy strategy,
            Set<String> changedPaths
        ) {
            this.id = id;
            this.title = validateText(title, "Pull Request title");
            this.author = validateText(author, "Author");
            this.sourceBranch = validateText(sourceBranch, "Source branch");
            this.targetBranch = validateText(targetBranch, "Target branch");
            this.baseCommit = validateText(baseCommit, "Base commit");
            this.headCommit = validateText(headCommit, "Head commit");
            this.state = draft ? PullRequestState.DRAFT : PullRequestState.OPEN;
            this.strategy = Objects.requireNonNull(strategy);
            this.changedPaths = Set.copyOf(changedPaths);
        }

        int id() {
            return id;
        }

        String author() {
            return author;
        }

        String sourceBranch() {
            return sourceBranch;
        }

        String targetBranch() {
            return targetBranch;
        }

        String headCommit() {
            return headCommit;
        }

        String baseCommit() {
            return baseCommit;
        }

        PullRequestState state() {
            return state;
        }

        MergeStrategy strategy() {
            return strategy;
        }

        List<Review> reviews() {
            return Collections.unmodifiableList(reviews);
        }

        Map<String, StatusCheck> checks() {
            return Collections.unmodifiableMap(checks);
        }

        Map<Integer, Discussion> discussions() {
            return Collections.unmodifiableMap(discussions);
        }

        Set<String> changedPaths() {
            return changedPaths;
        }

        void markReady() {
            requireState(PullRequestState.DRAFT);
            state = PullRequestState.OPEN;
        }

        void close() {
            if (state != PullRequestState.OPEN && state != PullRequestState.DRAFT) {
                throw new GovernanceException("Pull Request cannot be closed from this state.");
            }
            state = PullRequestState.CLOSED;
        }

        void reopen() {
            requireState(PullRequestState.CLOSED);
            state = PullRequestState.OPEN;
        }

        void addReview(Review review) {
            requireState(PullRequestState.OPEN);
            reviews.add(review);
        }

        void addCheck(StatusCheck check) {
            if (state != PullRequestState.OPEN && state != PullRequestState.DRAFT) {
                throw new GovernanceException("Pull Request is not accepting check updates.");
            }
            checks.put(check.context() + ":" + check.commitId(), check);
        }

        int addDiscussion(String author, String path, int line, String body) {
            requireState(PullRequestState.OPEN);
            String normalized = validatePath(path);
            if (!changedPaths.contains(normalized)) {
                throw new GovernanceException("Discussion path is not part of the changeset.");
            }

            int discussionId = nextDiscussionId++;
            discussions.put(
                discussionId,
                new Discussion(discussionId, author, normalized, line, body, false)
            );
            return discussionId;
        }

        void resolveDiscussion(int discussionId) {
            Discussion current = discussions.get(discussionId);
            if (current == null) {
                throw new GovernanceException("Discussion does not exist.");
            }
            discussions.put(discussionId, current.resolve());
        }

        void updateHead(String newHead, String newBase, Set<String> newPaths,
                        boolean dismissStaleApprovals) {
            requireState(PullRequestState.OPEN);
            headCommit = validateText(newHead, "New head commit");
            baseCommit = validateText(newBase, "New base commit");
            changedPaths = Set.copyOf(newPaths);

            if (dismissStaleApprovals) {
                for (int index = 0; index < reviews.size(); index++) {
                    Review review = reviews.get(index);
                    if (review.decision() == ReviewDecision.APPROVED) {
                        reviews.set(index, new Review(
                            review.id(),
                            review.reviewer(),
                            ReviewDecision.STALE,
                            review.reviewedCommit(),
                            review.sequence()
                        ));
                    }
                }
            }
        }

        void setConflictState(boolean value) {
            conflicted = value;
        }

        boolean conflicted() {
            return conflicted;
        }

        void markMerged(String mergeCommit) {
            requireState(PullRequestState.OPEN);
            mergedCommit = validateText(mergeCommit, "Merge commit");
            state = PullRequestState.MERGED;
        }

        String mergedCommit() {
            return mergedCommit;
        }

        private void requireState(PullRequestState expected) {
            if (state != expected) {
                throw new GovernanceException(
                    "Expected state " + expected + " but found " + state
                );
            }
        }
    }

    record EligibilityReport(boolean eligible, List<String> blockers,
                             boolean administrativeBypass) {
        EligibilityReport {
            blockers = List.copyOf(blockers);
        }
    }

    static final class Repository {
        private final String name;
        private final Map<String, RepositoryMember> members = new HashMap<>();
        private final Map<String, Branch> branches = new HashMap<>();
        private final Map<String, BranchPolicy> policies = new HashMap<>();
        private final Map<Integer, PullRequest> pullRequests = new LinkedHashMap<>();
        private final AtomicInteger prSequence = new AtomicInteger();
        private final AtomicInteger reviewSequence = new AtomicInteger();

        Repository(String name, List<RepositoryMember> repositoryMembers) {
            this.name = validateText(name, "Repository name");
            for (RepositoryMember member : repositoryMembers) {
                if (members.putIfAbsent(member.username(), member) != null) {
                    throw new GovernanceException("Duplicate repository member.");
                }
            }
            branches.put("main", new Branch("main", "root-commit", false));
        }

        void addMember(RepositoryMember member) {
            if (members.putIfAbsent(member.username(), member) != null) {
                throw new GovernanceException("Member already exists.");
            }
        }

        RepositoryMember member(String username) {
            RepositoryMember member = members.get(username);
            if (member == null || !member.active()) {
                throw new GovernanceException("Unknown or inactive member: " + username);
            }
            return member;
        }

        void protectBranch(String branchName, BranchPolicy policy) {
            Branch branch = branches.get(branchName);
            if (branch == null || branch.deleted()) {
                throw new GovernanceException("Cannot protect an unavailable branch.");
            }
            policies.put(branchName, Objects.requireNonNull(policy));
        }

        void createBranch(String branchName, String fromBranch) {
            Branch source = branches.get(fromBranch);
            if (source == null || source.deleted() || branches.containsKey(branchName)) {
                throw new GovernanceException("Invalid branch creation request.");
            }
            branches.put(branchName, new Branch(branchName, source.headCommit(), false));
        }

        void updateBranchHead(String branchName, String newHead, String actor,
                              boolean forcePush) {
            RepositoryMember member = member(actor);
            Branch branch = branches.get(branchName);
            if (branch == null || branch.deleted()) {
                throw new GovernanceException("Branch is unavailable.");
            }
            if (member.role() == Role.READ) {
                throw new GovernanceException("Read-only member cannot push.");
            }

            BranchPolicy policy = policies.get(branchName);
            if (policy != null) {
                if (!policy.allowDirectPush() && !policy.permitsBypass(member.role())) {
                    throw new GovernanceException("Direct push is prohibited.");
                }
                if (forcePush && !policy.allowForcePush()) {
                    throw new GovernanceException("Force push is prohibited.");
                }
            }

            branches.put(branchName, branch.withHead(validateText(newHead, "New commit")));
        }

        PullRequest openPullRequest(
            String title,
            String author,
            String source,
            String target,
            boolean draft,
            MergeStrategy strategy,
            Set<String> changedPaths
        ) {
            member(author);
            Branch sourceBranch = branches.get(source);
            Branch targetBranch = branches.get(target);

            if (sourceBranch == null || targetBranch == null ||
                sourceBranch.deleted() || targetBranch.deleted() ||
                source.equals(target)) {
                throw new GovernanceException("Invalid Pull Request branches.");
            }
            if (sourceBranch.headCommit().equals(targetBranch.headCommit())) {
                throw new GovernanceException("There are no proposed changes.");
            }

            int id = prSequence.incrementAndGet();
            PullRequest pr = new PullRequest(
                id,
                title,
                author,
                source,
                target,
                targetBranch.headCommit(),
                sourceBranch.headCommit(),
                draft,
                strategy,
                changedPaths.stream()
                    .map(RepositoryQualityGovernance::validatePath)
                    .collect(Collectors.toSet())
            );
            pullRequests.put(id, pr);
            return pr;
        }

        PullRequest pullRequest(int id) {
            PullRequest pr = pullRequests.get(id);
            if (pr == null) {
                throw new GovernanceException("Pull Request does not exist.");
            }
            return pr;
        }

        void requestReview(int id, String actor, String reviewer) {
            PullRequest pr = pullRequest(id);
            member(actor);
            RepositoryMember candidate = member(reviewer);

            if (pr.state() != PullRequestState.OPEN ||
                reviewer.equals(pr.author()) ||
                !candidate.canReview()) {
                throw new GovernanceException("Invalid review request.");
            }
        }

        Review submitReview(int id, String reviewer, ReviewDecision decision) {
            PullRequest pr = pullRequest(id);
            RepositoryMember candidate = member(reviewer);

            if (reviewer.equals(pr.author()) ||
                !candidate.canReview() ||
                (decision != ReviewDecision.COMMENTED &&
                 decision != ReviewDecision.APPROVED &&
                 decision != ReviewDecision.CHANGES_REQUESTED)) {
                throw new GovernanceException("Reviewer or submitted decision is invalid.");
            }

            Review review = new Review(
                reviewSequence.incrementAndGet(),
                reviewer,
                decision,
                pr.headCommit(),
                reviewSequence.get()
            );
            pr.addReview(review);
            return review;
        }

        void dismissReview(int id, int reviewId, String actor) {
            PullRequest pr = pullRequest(id);
            if (!member(actor).canAdminister()) {
                throw new GovernanceException("Actor cannot dismiss reviews.");
            }

            List<Review> updated = new ArrayList<>(pr.reviews());
            boolean found = false;
            for (int i = 0; i < updated.size(); i++) {
                Review review = updated.get(i);
                if (review.id() == reviewId) {
                    updated.set(i, new Review(
                        review.id(),
                        review.reviewer(),
                        ReviewDecision.DISMISSED,
                        review.reviewedCommit(),
                        review.sequence()
                    ));
                    found = true;
                    break;
                }
            }
            if (!found) {
                throw new GovernanceException("Review does not exist.");
            }

            for (Review review : updated) {
                if (review.id() == reviewId) {
                    pr.addReview(review);
                    return;
                }
            }
        }

        int addDiscussion(int id, String author, String path, int line, String body) {
            RepositoryMember member = member(author);
            if (member.role() == Role.READ) {
                throw new GovernanceException("Read-only members cannot comment.");
            }
            return pullRequest(id).addDiscussion(author, path, line, body);
        }

        void resolveDiscussion(int id, int discussionId, String actor) {
            if (member(actor).role() == Role.READ) {
                throw new GovernanceException("Read-only members cannot resolve discussions.");
            }
            pullRequest(id).resolveDiscussion(discussionId);
        }

        void recordCheck(int id, String context, CheckState state, String commitId) {
            pullRequest(id).addCheck(new StatusCheck(context, commitId, state));
        }

        void refreshPullRequest(int id, String newHead, String newBase,
                                Set<String> newPaths) {
            PullRequest pr = pullRequest(id);
            BranchPolicy policy = policies.get(pr.targetBranch());
            pr.updateHead(
                newHead,
                newBase,
                newPaths,
                policy != null && policy.dismissStaleApprovals()
            );
        }

        void synchronizeBase(int id, String synchronizedHead, String targetHead,
                             Set<String> changedPaths) {
            PullRequest pr = pullRequest(id);
            refreshPullRequest(id, synchronizedHead, targetHead, changedPaths);
            pr.setConflictState(false);
        }

        void closePullRequest(int id, String actor) {
            PullRequest pr = pullRequest(id);
            RepositoryMember member = member(actor);
            if (!actor.equals(pr.author()) && member.role() == Role.READ) {
                throw new GovernanceException("Actor cannot close this Pull Request.");
            }
            pr.close();
        }

        void reopenPullRequest(int id, String actor) {
            PullRequest pr = pullRequest(id);
            RepositoryMember member = member(actor);
            if (!actor.equals(pr.author()) && member.role() == Role.READ) {
                throw new GovernanceException("Actor cannot reopen this Pull Request.");
            }
            pr.reopen();
        }

        Map<String, Review> latestReviewByReviewer(PullRequest pr) {
            Map<String, Review> latest = new HashMap<>();
            for (Review review : pr.reviews()) {
                Review current = latest.get(review.reviewer());
                if (current == null || review.sequence() > current.sequence()) {
                    latest.put(review.reviewer(), review);
                }
            }
            return latest;
        }

        EligibilityReport evaluateMerge(int id, String actor) {
            PullRequest pr = pullRequest(id);
            RepositoryMember actorMember = member(actor);
            Branch source = branches.get(pr.sourceBranch());
            Branch target = branches.get(pr.targetBranch());

            BranchPolicy policy = policies.getOrDefault(
                pr.targetBranch(),
                new BranchPolicy(
                    0, Set.of(), List.of(), true,
                    false, false, true, false, false,
                    true, Set.of()
                )
            );

            List<String> blockers = new ArrayList<>();
            if (pr.state() != PullRequestState.OPEN) {
                blockers.add("Pull Request is not open.");
            }
            if (source == null || source.deleted() ||
                target == null || target.deleted()) {
                blockers.add("Source or target branch is unavailable.");
                return new EligibilityReport(false, blockers, false);
            }
            if (!source.headCommit().equals(pr.headCommit())) {
                blockers.add("Source branch contains unreviewed commits.");
            }
            if (!target.headCommit().equals(pr.baseCommit())) {
                blockers.add("Target branch has advanced.");
            }
            if (pr.conflicted()) {
                blockers.add("Merge conflicts remain unresolved.");
            }

            boolean bypass = policy.permitsBypass(actorMember.role());
            if (!bypass) {
                for (String required : policy.requiredChecks()) {
                    StatusCheck check = pr.checks().get(
                        required + ":" + pr.headCommit()
                    );
                    if (check == null || check.state() != CheckState.SUCCESS) {
                        blockers.add("Required check has not succeeded: " + required);
                    }
                }

                Map<String, Review> latest = latestReviewByReviewer(pr);
                List<Review> eligibleReviews = latest.values().stream()
                    .filter(review -> {
                        RepositoryMember reviewer = members.get(review.reviewer());
                        return reviewer != null
                            && reviewer.active()
                            && reviewer.role() != Role.READ
                            && !review.reviewer().equals(pr.author())
                            && (!policy.dismissStaleApprovals()
                                || review.reviewedCommit().equals(pr.headCommit()));
                    })
                    .toList();

                long changesRequested = eligibleReviews.stream()
                    .filter(review -> review.decision() == ReviewDecision.CHANGES_REQUESTED)
                    .count();
                if (changesRequested > 0) {
                    blockers.add("One or more reviewers have requested changes.");
                }

                long approvals = eligibleReviews.stream()
                    .filter(review -> review.decision() == ReviewDecision.APPROVED)
                    .count();

                if (approvals < policy.requiredApprovals()) {
                    blockers.add(
                        "Insufficient approvals: " + approvals +
                        "/" + policy.requiredApprovals()
                    );
                }

                for (ApprovalRequirement requirement : policy.roleRequirements()) {
                    long roleApprovals = eligibleReviews.stream()
                        .filter(review -> review.decision() == ReviewDecision.APPROVED)
                        .filter(review -> members.get(review.reviewer()).role()
                            == requirement.reviewerRole())
                        .count();

                    if (roleApprovals < requirement.minimumCount()) {
                        blockers.add(
                            "Role-specific approval requirement not met for " +
                            requirement.reviewerRole()
                        );
                    }
                }

                if (policy.requireResolvedDiscussions()) {
                    long unresolved = pr.discussions().values().stream()
                        .filter(discussion -> !discussion.resolved())
                        .count();
                    if (unresolved > 0) {
                        blockers.add(
                            unresolved + " discussion thread(s) remain unresolved."
                        );
                    }
                }

                if (policy.requireLinearHistory() &&
                    pr.strategy() == MergeStrategy.MERGE) {
                    blockers.add("Merge strategy violates linear-history policy.");
                }
            }

            return new EligibilityReport(blockers.isEmpty(), blockers, bypass);
        }

        String merge(int id, String actor, String resultingCommit) {
            PullRequest pr = pullRequest(id);
            EligibilityReport report = evaluateMerge(id, actor);

            if (!report.eligible()) {
                throw new GovernanceException(
                    "Merge blocked: " + String.join("; ", report.blockers())
                );
            }

            Branch target = branches.get(pr.targetBranch());
            branches.put(
                target.name(),
                target.withHead(validateText(resultingCommit, "Merge commit"))
            );
            pr.markMerged(resultingCommit);
            return resultingCommit;
        }

        String name() {
            return name;
        }
    }

    private static String validateText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new GovernanceException(field + " cannot be empty.");
        }
        return value.trim();
    }

    private static String validatePath(String path) {
        String normalized = validateText(path, "Repository path").replace('\\', '/');
        if (normalized.startsWith("/") || normalized.contains("\0")) {
            throw new GovernanceException("Unsafe repository path.");
        }
        for (String segment : normalized.split("/")) {
            if (segment.isEmpty() || segment.equals("..")) {
                throw new GovernanceException("Unsafe repository path.");
            }
        }
        return normalized;
    }

    public static void main(String[] args) {
        try {
            Repository repository = new Repository(
                "enterprise-quality-platform",
                List.of(
                    new RepositoryMember("developer", Role.WRITE, true),
                    new RepositoryMember("reviewer", Role.MAINTAIN, true),
                    new RepositoryMember("administrator", Role.ADMIN, true)
                )
            );

            BranchPolicy policy = new BranchPolicy(
                1,
                Set.of("unit-tests", "security-scan"),
                List.of(new ApprovalRequirement(Role.MAINTAIN, 1)),
                true,
                true,
                true,
                false,
                false,
                false,
                true,
                Set.of()
            );

            repository.protectBranch("main", policy);
            repository.createBranch("feature/quality-controls", "main");

            repository.updateBranchHead(
                "feature/quality-controls",
                "feature-commit-101",
                "developer",
                false
            );

            PullRequest pr = repository.openPullRequest(
                "Introduce repository quality controls",
                "developer",
                "feature/quality-controls",
                "main",
                false,
                MergeStrategy.SQUASH,
                Set.of("src/quality/ReviewPolicy.java", "test/ReviewPolicyTest.java")
            );

            repository.requestReview(pr.id(), "developer", "reviewer");
            repository.submitReview(pr.id(), "reviewer", ReviewDecision.APPROVED);

            int discussionId = repository.addDiscussion(
                pr.id(),
                "reviewer",
                "src/quality/ReviewPolicy.java",
                28,
                "Reviewer eligibility and stale decisions are explicitly checked."
            );
            repository.resolveDiscussion(pr.id(), discussionId, "developer");

            repository.recordCheck(
                pr.id(), "unit-tests", CheckState.SUCCESS, pr.headCommit()
            );
            repository.recordCheck(
                pr.id(), "security-scan", CheckState.SUCCESS, pr.headCommit()
            );

            EligibilityReport report =
                repository.evaluateMerge(pr.id(), "developer");

            System.out.println("Repository: " + repository.name());
            System.out.println("Pull Request: #" + pr.id());
            System.out.println("Merge eligible: " + report.eligible());

            report.blockers().forEach(
                blocker -> System.out.println("Blocker: " + blocker)
            );

            if (report.eligible()) {
                repository.merge(pr.id(), "developer", "merge-commit-202");
                System.out.println("Pull Request state: " + pr.state());
                System.out.println("Merge commit: " + pr.mergedCommit());
            }
        } catch (GovernanceException exception) {
            System.err.println("Governance failure: " + exception.getMessage());
            System.exitCode = 1;
        }
    }
}
