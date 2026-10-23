import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

public class RepositoryGovernance {

    enum PullRequestState {
        DRAFT, OPEN, CLOSED, MERGED
    }

    enum ReviewState {
        COMMENTED, APPROVED, CHANGES_REQUESTED, DISMISSED
    }

    enum MergeStrategy {
        MERGE_COMMIT, SQUASH, REBASE
    }

    enum CheckState {
        PASSED, FAILED, PENDING
    }

    record Commit(String sha, String message, String author) {
        Commit {
            requireText(sha, "Commit SHA");
            requireText(message, "Commit message");
            requireText(author, "Commit author");
        }
    }

    record Review(
        String reviewer,
        ReviewState state,
        String commitSha,
        List<String> comments,
        boolean dismissed
    ) {
        Review {
            requireText(reviewer, "Reviewer");
            requireText(commitSha, "Reviewed commit");
            comments = List.copyOf(comments == null ? List.of() : comments);
        }

        Review dismiss() {
            return new Review(
                reviewer,
                ReviewState.DISMISSED,
                commitSha,
                comments,
                true
            );
        }
    }

    record StatusCheck(
        String name,
        CheckState state,
        String commitSha
    ) {
        StatusCheck {
            requireText(name, "Status check name");
            requireText(commitSha, "Status check revision");
        }
    }

    record BranchProtectionPolicy(
        int requiredReviews,
        Set<String> requiredStatusChecks,
        boolean requireConversationResolution,
        boolean requireLinearHistory,
        boolean allowDirectPush,
        boolean allowForcePush,
        boolean allowDeletion,
        boolean allowAdministratorBypass
    ) {
        BranchProtectionPolicy {
            if (requiredReviews < 0) {
                throw new IllegalArgumentException(
                    "Required review count cannot be negative."
                );
            }

            requiredStatusChecks =
                Collections.unmodifiableSet(new HashSet<>(requiredStatusChecks));
        }
    }

    record MergeDecision(
        boolean eligible,
        List<String> failures
    ) {
        MergeDecision {
            failures = List.copyOf(failures);
        }
    }

    static final class PullRequest {
        private final int number;
        private final String title;
        private final String sourceBranch;
        private final String targetBranch;
        private final String author;

        private PullRequestState state;
        private final List<Commit> commits = new ArrayList<>();
        private final Set<String> requestedReviewers = new HashSet<>();
        private final List<Review> reviews = new ArrayList<>();
        private final Map<String, StatusCheck> statusChecks = new HashMap<>();

        private int unresolvedConversations;
        private String headSha = "";

        PullRequest(
            int number,
            String title,
            String sourceBranch,
            String targetBranch,
            String author,
            boolean draft
        ) {
            this.number = number;
            this.title = requireText(title, "Pull Request title");
            this.sourceBranch = requireText(sourceBranch, "Source branch");
            this.targetBranch = requireText(targetBranch, "Target branch");
            this.author = requireText(author, "Pull Request author");

            if (sourceBranch.equals(targetBranch)) {
                throw new IllegalArgumentException(
                    "Source and target branches must differ."
                );
            }

            this.state = draft
                ? PullRequestState.DRAFT
                : PullRequestState.OPEN;
        }

        int number() {
            return number;
        }

        String author() {
            return author;
        }

        String headSha() {
            return headSha;
        }

        PullRequestState state() {
            return state;
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        List<Commit> commits() {
            return List.copyOf(commits);
        }

        Map<String, StatusCheck> statusChecks() {
            return Map.copyOf(statusChecks);
        }

        int unresolvedConversations() {
            return unresolvedConversations;
        }

        void open() {
            if (state != PullRequestState.DRAFT &&
                state != PullRequestState.CLOSED) {
                throw new IllegalStateException(
                    "Pull Request cannot be opened from its current state."
                );
            }

            state = PullRequestState.OPEN;
        }

        void close() {
            if (state == PullRequestState.MERGED) {
                throw new IllegalStateException(
                    "Merged Pull Request cannot be closed."
                );
            }

            state = PullRequestState.CLOSED;
        }

        void reopen() {
            if (state != PullRequestState.CLOSED) {
                throw new IllegalStateException(
                    "Only closed Pull Requests can be reopened."
                );
            }

            state = PullRequestState.OPEN;
        }

        void addCommit(Commit commit) {
            requireOpenOrDraftModification();

            if (commits.stream().anyMatch(
                existing -> existing.sha().equals(commit.sha())
            )) {
                throw new IllegalArgumentException(
                    "Duplicate commit SHA."
                );
            }

            commits.add(commit);
            headSha = commit.sha();

            // Approvals belong to a reviewed revision. A new revision makes
            // prior approvals stale unless the organization explicitly
            // chooses to preserve them.
            for (int i = 0; i < reviews.size(); i++) {
                Review review = reviews.get(i);

                if (
                    review.state() == ReviewState.APPROVED &&
                    !review.commitSha().equals(headSha)
                ) {
                    reviews.set(i, review.dismiss());
                }
            }
        }

        void requestReview(String reviewer) {
            requireText(reviewer, "Reviewer");

            if (reviewer.equals(author)) {
                throw new IllegalArgumentException(
                    "The author cannot be a required reviewer."
                );
            }

            requestedReviewers.add(reviewer);
        }

        void submitReview(
            String reviewer,
            ReviewState state,
            List<String> comments
        ) {
            if (this.state != PullRequestState.OPEN) {
                throw new IllegalStateException(
                    "Reviews require an open Pull Request."
                );
            }

            if (reviewer.equals(author)) {
                throw new IllegalArgumentException(
                    "Self-review is not permitted."
                );
            }

            reviews.add(
                new Review(
                    reviewer,
                    state,
                    headSha,
                    comments,
                    false
                )
            );
        }

        void setStatusCheck(String name, CheckState state) {
            requireText(name, "Status check name");

            if (headSha.isBlank()) {
                throw new IllegalStateException(
                    "Status checks require a current revision."
                );
            }

            statusChecks.put(
                name,
                new StatusCheck(name, state, headSha)
            );
        }

        void addConversation() {
            unresolvedConversations++;
        }

        void resolveConversation() {
            if (unresolvedConversations == 0) {
                throw new IllegalStateException(
                    "No unresolved conversation exists."
                );
            }

            unresolvedConversations--;
        }

        void merge() {
            if (state != PullRequestState.OPEN) {
                throw new IllegalStateException(
                    "Only open Pull Requests can be merged."
                );
            }

            state = PullRequestState.MERGED;
        }

        private void requireOpenOrDraftModification() {
            if (state != PullRequestState.OPEN &&
                state != PullRequestState.DRAFT) {
                throw new IllegalStateException(
                    "The Pull Request cannot be modified in its current state."
                );
            }
        }
    }

    static final class GovernanceService {
        private final BranchProtectionPolicy policy;

        GovernanceService(BranchProtectionPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        MergeDecision evaluate(PullRequest pr) {
            List<String> failures = new ArrayList<>();

            if (pr.state() != PullRequestState.OPEN) {
                failures.add("Pull Request must be open.");
            }

            if (pr.commits().isEmpty()) {
                failures.add("Pull Request contains no commits.");
            }

            Set<String> eligibleApprovers = new HashSet<>();

            for (Review review : pr.reviews()) {
                if (
                    review.state() == ReviewState.APPROVED &&
                    !review.dismissed() &&
                    review.commitSha().equals(pr.headSha()) &&
                    !review.reviewer().equals(pr.author())
                ) {
                    eligibleApprovers.add(review.reviewer());
                }
            }

            if (eligibleApprovers.size() < policy.requiredReviews()) {
                failures.add(
                    "The required number of current approvals has not been reached."
                );
            }

            boolean activeChangesRequested = pr.reviews().stream().anyMatch(
                review ->
                    review.state() == ReviewState.CHANGES_REQUESTED &&
                    !review.dismissed() &&
                    review.commitSha().equals(pr.headSha())
            );

            if (activeChangesRequested) {
                failures.add(
                    "An active changes-requested review remains."
                );
            }

            for (String requiredCheck : policy.requiredStatusChecks()) {
                StatusCheck check = pr.statusChecks().get(requiredCheck);

                if (
                    check == null ||
                    check.state() != CheckState.PASSED ||
                    !check.commitSha().equals(pr.headSha())
                ) {
                    failures.add(
                        "Required status check '" +
                        requiredCheck +
                        "' has not passed for the current revision."
                    );
                }
            }

            if (
                policy.requireConversationResolution() &&
                pr.unresolvedConversations() > 0
            ) {
                failures.add(
                    "Review conversations remain unresolved."
                );
            }

            return new MergeDecision(
                failures.isEmpty(),
                failures
            );
        }

        void merge(
            PullRequest pr,
            MergeStrategy strategy
        ) {
            MergeDecision decision = evaluate(pr);

            if (!decision.eligible()) {
                throw new IllegalStateException(
                    "Merge blocked: " +
                    String.join("; ", decision.failures())
                );
            }

            pr.merge();

            System.out.println(
                "PR #" + pr.number() +
                " merged using " +
                strategy.name().toLowerCase() +
                " strategy."
            );
        }
    }

    private static String requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(
                field + " cannot be blank."
            );
        }
        return value;
    }

    public static void main(String[] args) {
        BranchProtectionPolicy policy =
            new BranchProtectionPolicy(
                2,
                Set.of("tests", "security"),
                true,
                true,
                false,
                false,
                false,
                false
            );

        GovernanceService governance =
            new GovernanceService(policy);

        PullRequest pr =
            new PullRequest(
                42,
                "Harden payment authorization",
                "feature/payment-policy",
                "main",
                "alice",
                true
            );

        pr.addCommit(
            new Commit(
                "a100",
                "Add authorization policy",
                "alice"
            )
        );

        pr.requestReview("bob");
        pr.requestReview("carol");
        pr.open();

        pr.submitReview(
            "bob",
            ReviewState.APPROVED,
            List.of("Policy boundaries are clear.")
        );

        pr.submitReview(
            "carol",
            ReviewState.CHANGES_REQUESTED,
            List.of("Add expired credential regression coverage.")
        );

        pr.addConversation();
        pr.setStatusCheck("tests", CheckState.PASSED);
        pr.setStatusCheck("security", CheckState.PASSED);

        MergeDecision firstDecision = governance.evaluate(pr);

        System.out.println(
            "Initial eligibility: " + firstDecision.eligible()
        );

        firstDecision.failures().forEach(
            failure -> System.out.println(" - " + failure)
        );

        // The new commit creates a new review revision.
        pr.addCommit(
            new Commit(
                "a101",
                "Add expired credential regression coverage",
                "alice"
            )
        );

        pr.submitReview(
            "bob",
            ReviewState.APPROVED,
            List.of("Regression coverage is present.")
        );

        pr.submitReview(
            "carol",
            ReviewState.APPROVED,
            List.of("Requested change has been addressed.")
        );

        pr.resolveConversation();
        pr.setStatusCheck("tests", CheckState.PASSED);
        pr.setStatusCheck("security", CheckState.PASSED);

        MergeDecision finalDecision = governance.evaluate(pr);

        System.out.println(
            "\nFinal eligibility: " + finalDecision.eligible()
        );

        if (finalDecision.eligible()) {
            governance.merge(pr, MergeStrategy.SQUASH);
        }
    }
}
