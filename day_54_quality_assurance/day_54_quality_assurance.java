import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeSet;
import java.util.stream.Collectors;

public class RepositoryGovernance {

    enum PullRequestState { OPEN, MERGED, CLOSED }
    enum ReviewState { COMMENTED, APPROVED, CHANGES_REQUESTED, DISMISSED }
    enum CheckState { PENDING, PASSED, FAILED }
    enum MergeStrategy { MERGE_COMMIT, SQUASH, REBASE }

    static final class GovernanceException extends RuntimeException {
        GovernanceException(String message) {
            super(message);
        }
    }

    record Commit(
        String id,
        String message,
        String author,
        List<String> parents
    ) {
        Commit {
            requireText(id, "Commit ID");
            requireText(message, "Commit message");
            requireText(author, "Commit author");
            parents = List.copyOf(parents);
        }
    }

    static final class Branch {
        private final String name;
        private final List<Commit> commits = new ArrayList<>();
        private final boolean protectedBranch;

        Branch(String name, List<Commit> initialCommits, boolean protectedBranch) {
            requireText(name, "Branch name");
            this.name = name;
            this.commits.addAll(initialCommits);
            this.protectedBranch = protectedBranch;
        }

        String name() { return name; }
        boolean protectedBranch() { return protectedBranch; }
        List<Commit> commits() { return Collections.unmodifiableList(commits); }

        String head() {
            return commits.isEmpty() ? null : commits.get(commits.size() - 1).id();
        }

        void append(Commit commit) {
            commits.add(Objects.requireNonNull(commit));
        }
    }

    record Review(
        String reviewer,
        ReviewState state,
        String commitId,
        List<String> comments,
        Instant submittedAt
    ) {
        Review {
            requireText(reviewer, "Reviewer");
            Objects.requireNonNull(state, "Review state");
            requireText(commitId, "Reviewed commit");
            comments = List.copyOf(comments);
            Objects.requireNonNull(submittedAt, "Submission timestamp");
        }
    }

    record StatusCheck(String name, CheckState state, String commitId) {
        StatusCheck {
            requireText(name, "Check name");
            Objects.requireNonNull(state, "Check state");
            requireText(commitId, "Check commit");
        }
    }

    record BranchProtectionPolicy(
        int requiredApprovals,
        Set<String> requiredChecks,
        boolean requireResolvedConversations,
        boolean requireLinearHistory,
        boolean allowDirectPush,
        boolean allowForcePush,
        boolean allowDeletion,
        boolean allowAdminBypass
    ) {
        BranchProtectionPolicy {
            if (requiredApprovals < 0) {
                throw new GovernanceException("Approval count cannot be negative.");
            }
            requiredChecks = Set.copyOf(requiredChecks);
        }
    }

    static final class PullRequest {
        private final int number;
        private final String author;
        private final Branch source;
        private final Branch target;
        private final Set<String> eligibleReviewers;
        private final BranchProtectionPolicy policy;
        private final List<Review> reviews = new ArrayList<>();
        private final Map<String, StatusCheck> checks = new HashMap<>();
        private final Map<String, Boolean> conversations = new HashMap<>();

        private PullRequestState state = PullRequestState.OPEN;
        private boolean draft;
        private String recordedBaseHead;
        private Commit mergeCommit;

        PullRequest(
            int number,
            String author,
            Branch source,
            Branch target,
            Set<String> eligibleReviewers,
            BranchProtectionPolicy policy,
            boolean draft
        ) {
            if (number <= 0) throw new GovernanceException("Invalid PR number.");
            requireText(author, "PR author");
            if (source.name().equals(target.name())) {
                throw new GovernanceException("Source and target must differ.");
            }
            if (eligibleReviewers.contains(author)) {
                throw new GovernanceException("Author cannot review their own PR.");
            }

            this.number = number;
            this.author = author;
            this.source = source;
            this.target = target;
            this.eligibleReviewers = Set.copyOf(eligibleReviewers);
            this.policy = Objects.requireNonNull(policy);
            this.draft = draft;
            this.recordedBaseHead = target.head();
        }

        private void requireOpen() {
            if (state != PullRequestState.OPEN) {
                throw new GovernanceException("PR is not open.");
            }
        }

        void addCommit(Commit commit) {
            requireOpen();
            if (!commit.author().equals(author)) {
                throw new GovernanceException("Unexpected commit author.");
            }
            if (source.commits().stream().anyMatch(c -> c.id().equals(commit.id()))) {
                throw new GovernanceException("Duplicate commit ID.");
            }
            source.append(commit);
        }

        void markReady() {
            requireOpen();
            draft = false;
        }

        void synchronizeBase() {
            requireOpen();
            recordedBaseHead = target.head();
        }

        void submitReview(Review review) {
            requireOpen();
            if (draft) throw new GovernanceException("Draft PR cannot be reviewed.");
            if (review.reviewer().equals(author) ||
                !eligibleReviewers.contains(review.reviewer())) {
                throw new GovernanceException("Reviewer is not eligible.");
            }
            if (review.state() == ReviewState.DISMISSED) {
                throw new GovernanceException("Cannot submit dismissed review.");
            }
            if (!Objects.equals(review.commitId(), source.head())) {
                throw new GovernanceException("Review must reference current HEAD.");
            }
            reviews.add(review);
        }

        void dismissLatestReview(String reviewer) {
            requireOpen();
            for (int i = reviews.size() - 1; i >= 0; i--) {
                Review old = reviews.get(i);
                if (old.reviewer().equals(reviewer) &&
                    old.state() != ReviewState.DISMISSED) {
                    reviews.set(i, new Review(
                        old.reviewer(),
                        ReviewState.DISMISSED,
                        old.commitId(),
                        old.comments(),
                        Instant.now()
                    ));
                    return;
                }
            }
            throw new GovernanceException("No active review exists.");
        }

        void recordCheck(String name, CheckState state) {
            requireOpen();
            checks.put(name, new StatusCheck(name, state, source.head()));
        }

        void openConversation(String id) {
            requireOpen();
            requireText(id, "Conversation ID");
            conversations.put(id, false);
        }

        void resolveConversation(String id) {
            requireOpen();
            if (!conversations.containsKey(id) || conversations.get(id)) {
                throw new GovernanceException("Conversation is missing or resolved.");
            }
            conversations.put(id, true);
        }

        private Map<String, Review> latestReviews() {
            Map<String, Review> latest = new HashMap<>();
            for (Review review : reviews) {
                latest.put(review.reviewer(), review);
            }
            return latest;
        }

        Set<String> currentApprovers() {
            return latestReviews().values().stream()
                .filter(review -> review.state() == ReviewState.APPROVED)
                .filter(review -> Objects.equals(review.commitId(), source.head()))
                .map(Review::reviewer)
                .collect(Collectors.toCollection(TreeSet::new));
        }

        List<String> evaluateMerge() {
            List<String> blockers = new ArrayList<>();

            if (state != PullRequestState.OPEN) {
                return List.of("PR is not open.");
            }
            if (draft) blockers.add("PR is still a draft.");
            if (source.commits().isEmpty()) blockers.add("Source branch is empty.");
            if (!Objects.equals(recordedBaseHead, target.head())) {
                blockers.add("Target changed; synchronize the base.");
            }

            Map<String, Review> latest = latestReviews();
            latest.values().stream()
                .filter(review -> Objects.equals(review.commitId(), source.head()))
                .filter(review -> review.state() == ReviewState.CHANGES_REQUESTED)
                .forEach(review -> blockers.add(
                    review.reviewer() + " requested changes."
                ));

            int approvals = currentApprovers().size();
            if (approvals < policy.requiredApprovals()) {
                blockers.add("Insufficient approvals: " + approvals);
            }

            for (String name : policy.requiredChecks()) {
                StatusCheck check = checks.get(name);
                if (check == null ||
                    check.state() != CheckState.PASSED ||
                    !Objects.equals(check.commitId(), source.head())) {
                    blockers.add("Required check is absent, failed, or stale: " + name);
                }
            }

            if (policy.requireResolvedConversations() &&
                conversations.values().stream().anyMatch(resolved -> !resolved)) {
                blockers.add("Unresolved review conversations remain.");
            }

            if (policy.requireLinearHistory()) {
                Set<String> ids = new HashSet<>();
                for (Commit commit : source.commits()) {
                    if (!ids.add(commit.id())) {
                        blockers.add("Duplicate commit ID in source history.");
                        break;
                    }
                    if (commit.parents().size() > 1) {
                        blockers.add("Merge commit violates linear-history policy.");
                        break;
                    }
                }
            }

            return blockers;
        }

        Commit merge(String actor, MergeStrategy strategy) {
            requireOpen();
            if (!eligibleReviewers.contains(actor) && !author.equals(actor)) {
                throw new GovernanceException("Actor cannot merge this PR.");
            }

            List<String> blockers = evaluateMerge();
            if (!blockers.isEmpty()) {
                throw new GovernanceException(
                    "Merge blocked: " + String.join("; ", blockers)
                );
            }

            List<String> parents = new ArrayList<>();
            if (target.head() != null) parents.add(target.head());

            if (strategy == MergeStrategy.MERGE_COMMIT && source.head() != null) {
                parents.add(source.head());
            }

            mergeCommit = new Commit(
                "merge-" + number,
                "Integrate PR #" + number + " using " + strategy,
                actor,
                parents
            );
            target.append(mergeCommit);
            state = PullRequestState.MERGED;
            return mergeCommit;
        }

        void close() {
            requireOpen();
            state = PullRequestState.CLOSED;
        }

        void reopen() {
            if (state != PullRequestState.CLOSED) {
                throw new GovernanceException("Only a closed PR can be reopened.");
            }
            state = PullRequestState.OPEN;
            recordedBaseHead = target.head();
        }

        PullRequestState state() { return state; }
        Commit mergeCommit() { return mergeCommit; }
    }

    static void directPush(
        Branch branch,
        Commit commit,
        BranchProtectionPolicy policy,
        boolean admin
    ) {
        if (branch.protectedBranch() && !policy.allowDirectPush() &&
            !(admin && policy.allowAdminBypass())) {
            throw new GovernanceException("Direct push denied by branch protection.");
        }
        branch.append(commit);
    }

    private static void requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new GovernanceException(field + " is required.");
        }
    }

    public static void main(String[] args) {
        BranchProtectionPolicy policy = new BranchProtectionPolicy(
            2,
            Set.of("unit-tests", "security-scan"),
            true,
            true,
            false,
            false,
            false,
            false
        );

        Branch main = new Branch(
            "main",
            List.of(new Commit(
                "c100", "Initial release", "maintainer", List.of()
            )),
            true
        );
        Branch feature = new Branch("feature/repository-quality", List.of(), false);

        PullRequest pr = new PullRequest(
            91,
            "developer",
            feature,
            main,
            Set.of("reviewer-a", "reviewer-b", "maintainer"),
            policy,
            true
        );

        pr.markReady();
        pr.addCommit(new Commit(
            "c101", "Validate incoming records", "developer", List.of()
        ));
        pr.openConversation("thread-1");

        pr.submitReview(new Review(
            "reviewer-a", ReviewState.APPROVED, "c101",
            List.of("Validation is clear."), Instant.now()
        ));
        pr.submitReview(new Review(
            "reviewer-b", ReviewState.APPROVED, "c101",
            List.of("Tests cover invalid input."), Instant.now()
        ));

        pr.recordCheck("unit-tests", CheckState.PASSED);
        pr.recordCheck("security-scan", CheckState.PASSED);

        System.out.println("Before resolving discussion: " + pr.evaluateMerge());
        pr.resolveConversation("thread-1");

        pr.addCommit(new Commit(
            "c102", "Reject malformed identifiers", "developer", List.of("c101")
        ));
        System.out.println("After source update: " + pr.evaluateMerge());

        pr.submitReview(new Review(
            "reviewer-a", ReviewState.APPROVED, "c102",
            List.of(), Instant.now()
        ));
        pr.submitReview(new Review(
            "reviewer-b", ReviewState.APPROVED, "c102",
            List.of(), Instant.now()
        ));
        pr.recordCheck("unit-tests", CheckState.PASSED);
        pr.recordCheck("security-scan", CheckState.PASSED);

        System.out.println("Final blockers: " + pr.evaluateMerge());
        Commit merged = pr.merge("maintainer", MergeStrategy.SQUASH);
        System.out.println("Merged commit: " + merged.id());
        System.out.println("PR state: " + pr.state());

        try {
            directPush(
                main,
                new Commit("c103", "Bypass review", "developer", List.of()),
                policy,
                false
            );
        } catch (GovernanceException exception) {
            System.out.println("Protection control: " + exception.getMessage());
        }
    }
}
