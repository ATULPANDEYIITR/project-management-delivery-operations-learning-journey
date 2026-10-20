import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class RepositoryGovernance {

    enum PullRequestState {
        DRAFT,
        OPEN,
        CLOSED,
        MERGED
    }

    enum ReviewState {
        COMMENTED,
        APPROVED,
        CHANGES_REQUESTED,
        DISMISSED
    }

    enum MergeStrategy {
        MERGE_COMMIT,
        SQUASH,
        REBASE
    }

    enum FailureCode {
        INVALID_STATE,
        NO_COMMITS,
        BASE_OUTDATED,
        MERGE_CONFLICT,
        REVIEW_REQUIRED,
        CHANGES_REQUESTED,
        CHECK_MISSING,
        CHECK_FAILED,
        CHECK_STALE,
        CONVERSATION_UNRESOLVED,
        STRATEGY_FORBIDDEN
    }

    record Commit(
        String sha,
        String message,
        int changedFiles,
        int additions,
        int deletions
    ) {
        Commit {
            if (sha == null || !sha.matches("[a-fA-F0-9]{7,40}")) {
                throw new IllegalArgumentException("Invalid commit SHA.");
            }
            if (message == null || message.isBlank()) {
                throw new IllegalArgumentException("Commit message is required.");
            }
            if (changedFiles < 0 || additions < 0 || deletions < 0) {
                throw new IllegalArgumentException(
                    "Commit metrics cannot be negative."
                );
            }
        }
    }

    record Review(
        String reviewer,
        ReviewState state,
        int revision,
        int inlineComments,
        Instant submittedAt
    ) {
        Review {
            if (reviewer == null || reviewer.isBlank()) {
                throw new IllegalArgumentException("Reviewer is required.");
            }
            if (inlineComments < 0) {
                throw new IllegalArgumentException(
                    "Comment count cannot be negative."
                );
            }
        }
    }

    record StatusCheck(
        String name,
        boolean passed,
        int revision,
        Instant completedAt
    ) {
        StatusCheck {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Status check name is required."
                );
            }
        }
    }

    record BranchProtectionPolicy(
        int requiredApprovals,
        Set<String> requiredChecks,
        boolean dismissStaleApprovals,
        boolean requireResolvedConversations,
        boolean restrictDirectPush,
        boolean allowForcePush,
        boolean allowBranchDeletion,
        boolean requireLinearHistory,
        Set<MergeStrategy> allowedStrategies
    ) {
        BranchProtectionPolicy {
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException(
                    "Required approvals cannot be negative."
                );
            }

            requiredChecks = Set.copyOf(requiredChecks);
            allowedStrategies = Set.copyOf(allowedStrategies);
        }
    }

    record GovernanceDecision(
        boolean eligible,
        List<String> reasons,
        int eligibleApprovals
    ) {}

    static final class PullRequest {
        private final int number;
        private final String sourceBranch;
        private final String targetBranch;
        private final String title;

        private PullRequestState state;
        private int revision = 1;
        private boolean synchronizedWithBase = true;
        private boolean mergeConflict;
        private int unresolvedConversations;

        private final List<Commit> commits = new ArrayList<>();
        private final List<Review> reviews = new ArrayList<>();
        private final Map<String, StatusCheck> checks = new HashMap<>();

        PullRequest(
            int number,
            String sourceBranch,
            String targetBranch,
            String title,
            boolean draft
        ) {
            if (number <= 0) {
                throw new IllegalArgumentException(
                    "PR number must be positive."
                );
            }

            if (sourceBranch == null ||
                targetBranch == null ||
                sourceBranch.isBlank() ||
                targetBranch.isBlank() ||
                sourceBranch.equals(targetBranch)) {
                throw new IllegalArgumentException(
                    "Source and target branches must be different."
                );
            }

            if (title == null || title.trim().length() < 5) {
                throw new IllegalArgumentException(
                    "PR title is too short."
                );
            }

            this.number = number;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.title = title.trim();
            this.state = draft
                ? PullRequestState.DRAFT
                : PullRequestState.OPEN;
        }

        void open() {
            requireState(PullRequestState.DRAFT);

            state = PullRequestState.OPEN;
        }

        void addCommit(Commit commit) {
            requireMutable();

            commits.add(commit);
            revision++;
            synchronizedWithBase = true;
        }

        void submitReview(Review review) {
            requireState(PullRequestState.OPEN);

            reviews.add(review);
        }

        void setStatusCheck(StatusCheck check) {
            checks.put(check.name(), check);
        }

        void updateBaseBranch(boolean conflicts) {
            requireState(PullRequestState.OPEN);

            revision++;
            synchronizedWithBase = false;
            mergeConflict = conflicts;
        }

        void synchronize() {
            requireState(PullRequestState.OPEN);

            synchronizedWithBase = true;
            mergeConflict = false;
        }

        void setUnresolvedConversations(int count) {
            if (count < 0) {
                throw new IllegalArgumentException(
                    "Conversation count cannot be negative."
                );
            }

            unresolvedConversations = count;
        }

        void close() {
            if (state == PullRequestState.MERGED) {
                throw new IllegalStateException(
                    "Merged PRs cannot be closed."
                );
            }

            state = PullRequestState.CLOSED;
        }

        void reopen() {
            requireState(PullRequestState.CLOSED);

            state = PullRequestState.OPEN;
        }

        void merge() {
            requireState(PullRequestState.OPEN);

            state = PullRequestState.MERGED;
        }

        private void requireMutable() {
            if (state != PullRequestState.DRAFT &&
                state != PullRequestState.OPEN) {
                throw new IllegalStateException(
                    "PR is not accepting source changes."
                );
            }
        }

        private void requireState(PullRequestState expected) {
            if (state != expected) {
                throw new IllegalStateException(
                    "Expected state " + expected +
                    " but found " + state + "."
                );
            }
        }

        int revision() {
            return revision;
        }

        PullRequestState state() {
            return state;
        }

        boolean hasCommits() {
            return !commits.isEmpty();
        }

        boolean synchronizedWithBase() {
            return synchronizedWithBase;
        }

        boolean mergeConflict() {
            return mergeConflict;
        }

        int unresolvedConversations() {
            return unresolvedConversations;
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        Map<String, StatusCheck> checks() {
            return Map.copyOf(checks);
        }

        int changedFiles() {
            return commits.stream()
                .mapToInt(Commit::changedFiles)
                .sum();
        }

        int estimatedReviewMinutes() {
            return Math.max(10, changedFiles() * 4);
        }

        int number() {
            return number;
        }

        String sourceBranch() {
            return sourceBranch;
        }

        String targetBranch() {
            return targetBranch;
        }

        String title() {
            return title;
        }
    }

    static final class MergeEligibilityService {
        private final BranchProtectionPolicy policy;

        MergeEligibilityService(BranchProtectionPolicy policy) {
            this.policy = policy;
        }

        GovernanceDecision evaluate(
            PullRequest pr,
            Set<String> eligibleReviewers,
            MergeStrategy strategy
        ) {
            List<String> failures = new ArrayList<>();

            if (pr.state() != PullRequestState.OPEN) {
                failures.add("PR must be open.");
            }

            if (!pr.hasCommits()) {
                failures.add("PR contains no commits.");
            }

            if (!pr.synchronizedWithBase()) {
                failures.add("PR is not synchronized with the base branch.");
            }

            if (pr.mergeConflict()) {
                failures.add("Merge conflicts remain.");
            }

            if (!policy.allowedStrategies().contains(strategy)) {
                failures.add(
                    "Selected merge strategy is prohibited."
                );
            }

            Map<String, Review> latestReviews = new HashMap<>();

            for (Review review : pr.reviews()) {
                latestReviews.put(review.reviewer(), review);
            }

            int approvals = 0;
            boolean changesRequested = false;

            for (Map.Entry<String, Review> entry : latestReviews.entrySet()) {
                String reviewer = entry.getKey();
                Review review = entry.getValue();

                if (!eligibleReviewers.contains(reviewer)) {
                    continue;
                }

                if (review.state() == ReviewState.CHANGES_REQUESTED) {
                    changesRequested = true;
                }

                boolean currentRevision =
                    review.revision() == pr.revision();

                if (review.state() == ReviewState.APPROVED &&
                    (!policy.dismissStaleApprovals() || currentRevision)) {
                    approvals++;
                }
            }

            if (changesRequested) {
                failures.add(
                    "An eligible reviewer currently requests changes."
                );
            }

            if (approvals < policy.requiredApprovals()) {
                failures.add(
                    "Required approvals: " +
                    policy.requiredApprovals() +
                    ", current eligible approvals: " +
                    approvals +
                    "."
                );
            }

            for (String checkName : policy.requiredChecks()) {
                StatusCheck check = pr.checks().get(checkName);

                if (check == null) {
                    failures.add(
                        "Required check '" + checkName + "' is missing."
                    );
                    continue;
                }

                if (!check.passed()) {
                    failures.add(
                        "Required check '" + checkName + "' failed."
                    );
                }

                if (policy.dismissStaleApprovals() &&
                    check.revision() != pr.revision()) {
                    failures.add(
                        "Required check '" + checkName + "' is stale."
                    );
                }
            }

            if (policy.requireResolvedConversations() &&
                pr.unresolvedConversations() > 0) {
                failures.add(
                    pr.unresolvedConversations() +
                    " review conversation(s) remain unresolved."
                );
            }

            return new GovernanceDecision(
                failures.isEmpty(),
                List.copyOf(failures),
                approvals
            );
        }
    }

    public static void main(String[] args) {
        BranchProtectionPolicy policy = new BranchProtectionPolicy(
            2,
            Set.of("unit-tests", "security-scan"),
            true,
            true,
            true,
            false,
            false,
            true,
            EnumSet.of(MergeStrategy.SQUASH)
        );

        PullRequest pr = new PullRequest(
            620,
            "feature/resource-cost-review",
            "main",
            "Review repository cost and resource impact",
            true
        );

        pr.open();

        pr.addCommit(new Commit(
            "1234567abcdef",
            "Add resource review model",
            8,
            240,
            35
        ));

        pr.addCommit(new Commit(
            "abcdef7123456",
            "Add repository governance rules",
            5,
            150,
            20
        ));

        int currentRevision = pr.revision();

        pr.submitReview(new Review(
            "alice",
            ReviewState.APPROVED,
            currentRevision,
            2,
            Instant.now()
        ));

        pr.submitReview(new Review(
            "bob",
            ReviewState.CHANGES_REQUESTED,
            currentRevision,
            3,
            Instant.now()
        ));

        pr.setStatusCheck(new StatusCheck(
            "unit-tests",
            true,
            pr.revision(),
            Instant.now()
        ));

        pr.setStatusCheck(new StatusCheck(
            "security-scan",
            true,
            pr.revision(),
            Instant.now()
        ));

        pr.setUnresolvedConversations(1);

        MergeEligibilityService service =
            new MergeEligibilityService(policy);

        Set<String> eligibleReviewers =
            Set.of("alice", "bob", "carol");

        GovernanceDecision decision =
            service.evaluate(
                pr,
                eligibleReviewers,
                MergeStrategy.SQUASH
            );

        System.out.println(
            "PR #" + pr.number() +
            " changes: " + pr.changedFiles()
        );
        System.out.println(
            "Estimated review effort: " +
            pr.estimatedReviewMinutes() +
            " minutes"
        );

        System.out.println(
            "Initial merge eligibility: " +
            decision.eligible()
        );

        decision.reasons().forEach(
            reason -> System.out.println("BLOCKED: " + reason)
        );

        // A new approval replaces Bob's previous decision for policy
        // evaluation. This models the latest-review semantics used by
        // enterprise review workflows.
        pr.submitReview(new Review(
            "bob",
            ReviewState.APPROVED,
            pr.revision(),
            1,
            Instant.now()
        ));

        pr.setUnresolvedConversations(0);

        decision = service.evaluate(
            pr,
            eligibleReviewers,
            MergeStrategy.SQUASH
        );

        System.out.println(
            "\nAfter review correction: " +
            decision.eligible()
        );

        if (decision.eligible()) {
            pr.merge();
            System.out.println(
                "PR #" + pr.number() +
                " merged into " +
                pr.targetBranch() +
                " using squash."
            );
        } else {
            decision.reasons().forEach(
                reason -> System.out.println("BLOCKED: " + reason)
            );
        }

        // Demonstrate that a merged PR cannot be reopened as an active
        // review object in this domain model.
        System.out.println("Final PR state: " + pr.state());
    }
}
