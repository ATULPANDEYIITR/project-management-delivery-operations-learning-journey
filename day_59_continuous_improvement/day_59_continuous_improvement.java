import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

public class ContinuousImprovementGovernance {

    enum PullRequestState {
        DRAFT, OPEN, CLOSED, MERGED
    }

    enum ReviewState {
        COMMENTED, APPROVED, CHANGES_REQUESTED, DISMISSED
    }

    enum CheckState {
        PENDING, SUCCESS, FAILURE
    }

    record Commit(String sha, String message, String author) {
        Commit {
            if (sha == null || !sha.matches("[A-Fa-f0-9]{7,40}")) {
                throw new IllegalArgumentException("Invalid commit SHA");
            }
            if (message == null || message.isBlank()) {
                throw new IllegalArgumentException("Commit message is required");
            }
            if (author == null || author.isBlank()) {
                throw new IllegalArgumentException("Commit author is required");
            }
        }
    }

    record Review(
            String reviewer,
            ReviewState state,
            String commitSha,
            String comment,
            Instant submittedAt
    ) {
        Review {
            Objects.requireNonNull(reviewer);
            Objects.requireNonNull(state);
            Objects.requireNonNull(commitSha);
            Objects.requireNonNull(submittedAt);
        }
    }

    record StatusCheck(
            String name,
            CheckState state,
            String commitSha,
            Instant updatedAt
    ) {}

    record BranchProtectionPolicy(
            int requiredApprovals,
            Set<String> requiredChecks,
            boolean requireResolvedConversations,
            boolean dismissStaleApprovals,
            boolean requireLinearHistory,
            boolean allowDirectPush,
            boolean allowForcePush
    ) {
        BranchProtectionPolicy {
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException(
                        "Approval requirement cannot be negative"
                );
            }
            requiredChecks = Set.copyOf(requiredChecks);
        }
    }

    static final class Branch {
        private final String name;
        private boolean protectedBranch;
        private final List<Commit> commits = new ArrayList<>();

        Branch(String name, boolean protectedBranch) {
            this.name = name;
            this.protectedBranch = protectedBranch;
        }

        String name() {
            return name;
        }

        boolean protectedBranch() {
            return protectedBranch;
        }

        void protect() {
            protectedBranch = true;
        }

        List<Commit> commits() {
            return commits;
        }
    }

    static final class PullRequest {
        private final int number;
        private final String title;
        private final String sourceBranch;
        private final String targetBranch;
        private final String author;
        private PullRequestState state;
        private boolean draft;
        private final List<Commit> proposedCommits;
        private final List<Review> reviews = new ArrayList<>();
        private final Map<String, StatusCheck> checks = new LinkedHashMap<>();
        private final Set<String> unresolvedConversations = new LinkedHashSet<>();

        PullRequest(
                int number,
                String title,
                String sourceBranch,
                String targetBranch,
                String author,
                boolean draft,
                List<Commit> proposedCommits
        ) {
            this.number = number;
            this.title = title;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.author = author;
            this.draft = draft;
            this.state = draft
                    ? PullRequestState.DRAFT
                    : PullRequestState.OPEN;
            this.proposedCommits = new ArrayList<>(proposedCommits);
        }

        int number() {
            return number;
        }

        String title() {
            return title;
        }

        String sourceBranch() {
            return sourceBranch;
        }

        String targetBranch() {
            return targetBranch;
        }

        String author() {
            return author;
        }

        PullRequestState state() {
            return state;
        }

        void state(PullRequestState state) {
            this.state = state;
        }

        boolean draft() {
            return draft;
        }

        List<Commit> proposedCommits() {
            return proposedCommits;
        }

        List<Review> reviews() {
            return reviews;
        }

        Map<String, StatusCheck> checks() {
            return checks;
        }

        Set<String> unresolvedConversations() {
            return unresolvedConversations;
        }

        String head() {
            if (proposedCommits.isEmpty()) {
                return null;
            }
            return proposedCommits.get(proposedCommits.size() - 1).sha();
        }
    }

    record MergeDecision(
            boolean eligible,
            List<String> blockingReasons,
            Set<String> currentApprovers
    ) {
        MergeDecision {
            blockingReasons = List.copyOf(blockingReasons);
            currentApprovers = Set.copyOf(currentApprovers);
        }
    }

    interface ReviewerEligibilityPolicy {
        boolean eligible(String reviewer, PullRequest pullRequest);
    }

    static final class DefaultReviewerEligibilityPolicy
            implements ReviewerEligibilityPolicy {

        private final Set<String> privilegedReviewers;

        DefaultReviewerEligibilityPolicy(Set<String> privilegedReviewers) {
            this.privilegedReviewers = Set.copyOf(privilegedReviewers);
        }

        @Override
        public boolean eligible(String reviewer, PullRequest pullRequest) {
            return !reviewer.equals(pullRequest.author())
                    && privilegedReviewers.contains(reviewer);
        }
    }

    static final class GovernanceService {
        private final Map<String, Branch> branches = new LinkedHashMap<>();
        private final Map<String, BranchProtectionPolicy> policies =
                new HashMap<>();
        private final Map<Integer, PullRequest> pullRequests =
                new LinkedHashMap<>();
        private final ReviewerEligibilityPolicy reviewerPolicy;
        private int nextPullRequest = 1;

        GovernanceService(ReviewerEligibilityPolicy reviewerPolicy) {
            this.reviewerPolicy = reviewerPolicy;
        }

        void createBranch(String name, boolean protectedBranch) {
            requireName(name, "branch");
            if (branches.containsKey(name)) {
                throw new GovernanceException(
                        "Branch already exists: " + name
                );
            }
            branches.put(name, new Branch(name, protectedBranch));
        }

        void addCommit(
                String branchName,
                Commit commit
        ) {
            Branch branch = branch(branchName);
            if (branch.commits().stream()
                    .anyMatch(existing -> existing.sha().equals(commit.sha()))) {
                throw new GovernanceException(
                        "Duplicate commit: " + commit.sha()
                );
            }
            branch.commits().add(commit);
        }

        void configureProtection(
                String branchName,
                BranchProtectionPolicy policy
        ) {
            Branch branch = branch(branchName);
            branch.protect();
            policies.put(branchName, policy);
        }

        PullRequest createPullRequest(
                String title,
                String source,
                String target,
                String author,
                boolean draft
        ) {
            if (title == null || title.isBlank()) {
                throw new GovernanceException("PR title is required");
            }
            if (source.equals(target)) {
                throw new GovernanceException(
                        "Source and target must differ"
                );
            }

            Branch sourceBranch = branch(source);
            branch(target);

            if (sourceBranch.commits().isEmpty()) {
                throw new GovernanceException(
                        "Source branch contains no changes"
                );
            }

            PullRequest pr = new PullRequest(
                    nextPullRequest++,
                    title.trim(),
                    source,
                    target,
                    author,
                    draft,
                    sourceBranch.commits()
            );

            pullRequests.put(pr.number(), pr);
            return pr;
        }

        void submitReview(
                int prNumber,
                String reviewer,
                ReviewState state,
                String comment
        ) {
            PullRequest pr = pullRequest(prNumber);
            ensureActive(pr);

            if (!reviewerPolicy.eligible(reviewer, pr)) {
                throw new GovernanceException(
                        "Reviewer is not eligible for this pull request"
                );
            }

            if (pr.head() == null) {
                throw new GovernanceException("PR has no head commit");
            }

            pr.reviews().add(
                    new Review(
                            reviewer,
                            state,
                            pr.head(),
                            comment == null ? "" : comment,
                            Instant.now()
                    )
            );
        }

        void updateStatus(
                int prNumber,
                String checkName,
                CheckState state
        ) {
            PullRequest pr = pullRequest(prNumber);
            ensureActive(pr);

            if (pr.head() == null) {
                throw new GovernanceException("PR has no head commit");
            }

            pr.checks().put(
                    checkName,
                    new StatusCheck(
                            checkName,
                            state,
                            pr.head(),
                            Instant.now()
                    )
            );
        }

        void openConversation(int prNumber, String conversationId) {
            PullRequest pr = pullRequest(prNumber);
            ensureActive(pr);
            pr.unresolvedConversations().add(conversationId);
        }

        void resolveConversation(int prNumber, String conversationId) {
            PullRequest pr = pullRequest(prNumber);
            if (!pr.unresolvedConversations().remove(conversationId)) {
                throw new GovernanceException(
                        "Conversation is not unresolved"
                );
            }
        }

        void synchronize(int prNumber) {
            PullRequest pr = pullRequest(prNumber);
            ensureActive(pr);

            Branch source = branch(pr.sourceBranch());
            pr.proposedCommits().clear();
            pr.proposedCommits().addAll(source.commits());

            BranchProtectionPolicy policy = policies.get(pr.targetBranch());
            if (policy != null && policy.dismissStaleApprovals()) {
                String head = pr.head();

                List<Review> updated = pr.reviews().stream()
                        .map(review -> {
                            if (review.state() == ReviewState.APPROVED
                                    && !review.commitSha().equals(head)) {
                                return new Review(
                                        review.reviewer(),
                                        ReviewState.DISMISSED,
                                        review.commitSha(),
                                        review.comment(),
                                        review.submittedAt()
                                );
                            }
                            return review;
                        })
                        .toList();

                pr.reviews().clear();
                pr.reviews().addAll(updated);
            }
        }

        MergeDecision evaluate(int prNumber) {
            PullRequest pr = pullRequest(prNumber);
            BranchProtectionPolicy policy = policies.get(
                    pr.targetBranch()
            );

            if (policy == null) {
                policy = new BranchProtectionPolicy(
                        0,
                        Set.of(),
                        false,
                        false,
                        false,
                        true,
                        false
                );
            }

            List<String> reasons = new ArrayList<>();

            if (pr.state() != PullRequestState.OPEN) {
                reasons.add("Pull request is not open");
            }

            if (pr.draft()) {
                reasons.add("Pull request is still a draft");
            }

            String head = pr.head();
            if (head == null) {
                reasons.add("No head commit exists");
            }

            final String evaluatedHead = head;

            Set<String> approvers = pr.reviews().stream()
                    .filter(review ->
                            review.state() == ReviewState.APPROVED
                                    && review.commitSha().equals(evaluatedHead)
                                    && reviewerPolicy.eligible(
                                            review.reviewer(), pr
                                    )
                    )
                    .map(Review::reviewer)
                    .collect(Collectors.toCollection(LinkedHashSet::new));

            if (approvers.size() < policy.requiredApprovals()) {
                reasons.add(
                        "Required approvals: "
                                + policy.requiredApprovals()
                                + ", current approvals: "
                                + approvers.size()
                );
            }

            for (String requiredCheck : policy.requiredChecks()) {
                StatusCheck check = pr.checks().get(requiredCheck);
                if (check == null
                        || !check.commitSha().equals(evaluatedHead)
                        || check.state() != CheckState.SUCCESS) {
                    reasons.add(
                            "Required check failed or is missing: "
                                    + requiredCheck
                    );
                }
            }

            if (policy.requireResolvedConversations()
                    && !pr.unresolvedConversations().isEmpty()) {
                reasons.add(
                        "Unresolved conversations: "
                                + pr.unresolvedConversations().size()
                );
            }

            return new MergeDecision(
                    reasons.isEmpty(),
                    reasons,
                    approvers
            );
        }

        void merge(int prNumber) {
            PullRequest pr = pullRequest(prNumber);
            MergeDecision decision = evaluate(prNumber);

            if (!decision.eligible()) {
                throw new GovernanceException(
                        "Merge blocked: "
                                + String.join("; ", decision.blockingReasons())
                );
            }

            Branch target = branch(pr.targetBranch());
            Branch source = branch(pr.sourceBranch());

            Set<String> existing = target.commits().stream()
                    .map(Commit::sha)
                    .collect(Collectors.toSet());

            for (Commit commit : source.commits()) {
                if (existing.add(commit.sha())) {
                    target.commits().add(commit);
                }
            }

            pr.state(PullRequestState.MERGED);
        }

        private Branch branch(String name) {
            Branch branch = branches.get(name);
            if (branch == null) {
                throw new GovernanceException(
                        "Unknown branch: " + name
                );
            }
            return branch;
        }

        private PullRequest pullRequest(int number) {
            PullRequest pr = pullRequests.get(number);
            if (pr == null) {
                throw new GovernanceException(
                        "Unknown pull request: " + number
                );
            }
            return pr;
        }

        private static void ensureActive(PullRequest pr) {
            if (pr.state() != PullRequestState.OPEN
                    && pr.state() != PullRequestState.DRAFT) {
                throw new GovernanceException(
                        "Pull request is " + pr.state()
                );
            }
        }

        private static void requireName(String value, String type) {
            if (value == null
                    || !value.matches("[A-Za-z0-9._/-]{2,100}")) {
                throw new GovernanceException(
                        "Invalid " + type + " name"
                );
            }
        }
    }

    static final class GovernanceException extends RuntimeException {
        GovernanceException(String message) {
            super(message);
        }
    }

    static void printDecision(
            PullRequest pr,
            MergeDecision decision
    ) {
        System.out.println();
        System.out.println("PR #" + pr.number() + ": " + pr.title());
        System.out.println(
                pr.sourceBranch() + " -> " + pr.targetBranch()
        );
        System.out.println("State: " + pr.state());
        System.out.println("Head: " + pr.head());
        System.out.println(
                "Merge eligible: " + decision.eligible()
        );

        if (!decision.blockingReasons().isEmpty()) {
            decision.blockingReasons().forEach(
                    reason -> System.out.println("  - " + reason)
            );
        }
    }

    public static void main(String[] args) {
        try {
            ReviewerEligibilityPolicy reviewerPolicy =
                    new DefaultReviewerEligibilityPolicy(
                            Set.of("reviewer-1", "reviewer-2", "security-reviewer")
                    );

            GovernanceService service =
                    new GovernanceService(reviewerPolicy);

            service.createBranch("main", true);
            service.createBranch("improvement/cycle-time", false);
            service.createBranch("improvement/review-quality", false);

            service.addCommit(
                    "main",
                    new Commit(
                            "a100001",
                            "Establish repository baseline",
                            "platform"
                    )
            );

            service.addCommit(
                    "improvement/cycle-time",
                    new Commit(
                            "b100001",
                            "Measure pull request cycle time",
                            "developer-1"
                    )
            );

            service.addCommit(
                    "improvement/cycle-time",
                    new Commit(
                            "b100002",
                            "Add process metrics",
                            "developer-1"
                    )
            );

            service.configureProtection(
                    "main",
                    new BranchProtectionPolicy(
                            2,
                            Set.of("unit-tests", "security-scan"),
                            true,
                            true,
                            true,
                            false,
                            false
                    )
            );

            PullRequest pr = service.createPullRequest(
                    "Reduce pull request cycle time",
                    "improvement/cycle-time",
                    "main",
                    "developer-1",
                    false
            );

            service.openConversation(pr.number(), "conversation-1");

            service.submitReview(
                    pr.number(),
                    "reviewer-1",
                    ReviewState.APPROVED,
                    "Metrics look correct."
            );

            service.submitReview(
                    pr.number(),
                    "reviewer-2",
                    ReviewState.CHANGES_REQUESTED,
                    "Clarify the baseline."
            );

            service.updateStatus(
                    pr.number(),
                    "unit-tests",
                    CheckState.SUCCESS
            );

            service.updateStatus(
                    pr.number(),
                    "security-scan",
                    CheckState.SUCCESS
            );

            printDecision(pr, service.evaluate(pr.number()));

            service.resolveConversation(
                    pr.number(),
                    "conversation-1"
            );

            service.submitReview(
                    pr.number(),
                    "reviewer-2",
                    ReviewState.APPROVED,
                    "Changes addressed."
            );

            MergeDecision decision = service.evaluate(pr.number());
            if (!decision.eligible()) {
                throw new GovernanceException(
                        String.join("; ", decision.blockingReasons())
                );
            }

            service.merge(pr.number());
            printDecision(pr, service.evaluate(pr.number()));

            service.addCommit(
                    "improvement/review-quality",
                    new Commit(
                            "c100001",
                            "Measure review turnaround",
                            "developer-2"
                    )
            );

            PullRequest second = service.createPullRequest(
                    "Improve review quality measurement",
                    "improvement/review-quality",
                    "main",
                    "developer-2",
                    false
            );

            service.submitReview(
                    second.number(),
                    "reviewer-1",
                    ReviewState.APPROVED,
                    ""
            );

            service.submitReview(
                    second.number(),
                    "reviewer-2",
                    ReviewState.APPROVED,
                    ""
            );

            service.updateStatus(
                    second.number(),
                    "unit-tests",
                    CheckState.SUCCESS
            );

            service.updateStatus(
                    second.number(),
                    "security-scan",
                    CheckState.SUCCESS
            );

            service.addCommit(
                    "improvement/review-quality",
                    new Commit(
                            "c100002",
                            "Correct turnaround calculation",
                            "developer-2"
                    )
            );

            service.synchronize(second.number());

            MergeDecision staleDecision =
                    service.evaluate(second.number());

            printDecision(second, staleDecision);

            if (staleDecision.eligible()) {
                throw new GovernanceException(
                        "Stale approvals should block the merge"
                );
            }

        } catch (GovernanceException | IllegalArgumentException ex) {
            System.err.println("Governance error: " + ex.getMessage());
            System.exit(1);
        }
    }
}
