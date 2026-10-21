import java.util.ArrayList;
import java.util.EnumSet;
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

    enum CheckState {
        PENDING, PASSED, FAILED
    }

    enum MergeStrategy {
        MERGE_COMMIT, SQUASH, REBASE
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
        String commitSha
    ) {
        Review {
            requireText(reviewer, "Reviewer");
            Objects.requireNonNull(state, "Review state is required");
            requireText(commitSha, "Reviewed commit SHA");
        }
    }

    record StatusCheck(
        String name,
        CheckState state,
        String commitSha
    ) {
        StatusCheck {
            requireText(name, "Status check name");
            Objects.requireNonNull(state, "Check state is required");
            requireText(commitSha, "Status-check commit SHA");
        }
    }

    record BranchProtection(
        String branch,
        int requiredReviews,
        Set<String> requiredChecks,
        boolean dismissStaleReviews,
        boolean requireConversationResolution,
        boolean restrictDirectPush,
        boolean allowForcePush,
        boolean allowDeletion,
        boolean requireLinearHistory,
        Set<MergeStrategy> allowedMergeStrategies,
        Set<String> bypassUsers
    ) {
        BranchProtection {
            requireText(branch, "Protected branch");

            if (requiredReviews < 0) {
                throw new IllegalArgumentException(
                    "Required reviews cannot be negative"
                );
            }

            requiredChecks = Set.copyOf(requiredChecks);
            allowedMergeStrategies = Set.copyOf(allowedMergeStrategies);
            bypassUsers = Set.copyOf(bypassUsers);
        }
    }

    record MergeDecision(
        boolean allowed,
        List<String> reasons
    ) {
        MergeDecision {
            reasons = List.copyOf(reasons);
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
        private final List<Review> reviews = new ArrayList<>();
        private final Map<String, StatusCheck> checks = new HashMap<>();
        private final Set<String> unresolvedConversations = new HashSet<>();

        private boolean mergeConflicts;
        private MergeStrategy mergeStrategy = MergeStrategy.SQUASH;
        private final String baseShaAtCreation;
        private String currentBaseSha;

        private PullRequest(
            int number,
            String title,
            String sourceBranch,
            String targetBranch,
            String author,
            PullRequestState state,
            String baseSha
        ) {
            this.number = number;
            this.title = title;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.author = author;
            this.state = state;
            this.baseShaAtCreation = baseSha;
            this.currentBaseSha = baseSha;
        }

        int number() {
            return number;
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

        PullRequestState state() {
            return state;
        }

        void setState(PullRequestState state) {
            this.state = Objects.requireNonNull(state);
        }

        List<Commit> commits() {
            return commits;
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

        boolean mergeConflicts() {
            return mergeConflicts;
        }

        void setMergeConflicts(boolean mergeConflicts) {
            this.mergeConflicts = mergeConflicts;
        }

        MergeStrategy mergeStrategy() {
            return mergeStrategy;
        }

        void setMergeStrategy(MergeStrategy strategy) {
            this.mergeStrategy = Objects.requireNonNull(strategy);
        }

        String baseShaAtCreation() {
            return baseShaAtCreation;
        }

        String currentBaseSha() {
            return currentBaseSha;
        }

        void setCurrentBaseSha(String sha) {
            this.currentBaseSha = sha;
        }

        Commit latestCommit() {
            if (commits.isEmpty()) {
                return null;
            }
            return commits.get(commits.size() - 1);
        }
    }

    static final class Repository {
        private final String name;
        private final Map<String, String> branches = new HashMap<>();
        private final Map<String, BranchProtection> protections = new HashMap<>();
        private final Map<Integer, PullRequest> pullRequests = new HashMap<>();
        private int nextPullRequestNumber = 1;

        Repository(String name) {
            this.name = requireText(name, "Repository name");
        }

        void createBranch(String name, String sha) {
            requireText(name, "Branch name");
            requireText(sha, "Branch SHA");

            if (branches.containsKey(name)) {
                throw new GovernanceException(
                    "Branch already exists: " + name
                );
            }

            branches.put(name, sha);
        }

        void protectBranch(BranchProtection policy) {
            if (!branches.containsKey(policy.branch())) {
                throw new GovernanceException(
                    "Cannot protect unknown branch: " + policy.branch()
                );
            }

            protections.put(policy.branch(), policy);
        }

        PullRequest createPullRequest(
            String title,
            String sourceBranch,
            String targetBranch,
            String author,
            boolean draft
        ) {
            requireText(title, "Pull Request title");
            requireText(sourceBranch, "Source branch");
            requireText(targetBranch, "Target branch");
            requireText(author, "Author");

            if (!branches.containsKey(sourceBranch)) {
                throw new GovernanceException(
                    "Unknown source branch: " + sourceBranch
                );
            }

            if (!branches.containsKey(targetBranch)) {
                throw new GovernanceException(
                    "Unknown target branch: " + targetBranch
                );
            }

            if (sourceBranch.equals(targetBranch)) {
                throw new IllegalArgumentException(
                    "Source and target branches must differ"
                );
            }

            int number = nextPullRequestNumber++;
            String baseSha = branches.get(targetBranch);

            PullRequest pr = new PullRequest(
                number,
                title,
                sourceBranch,
                targetBranch,
                author,
                draft ? PullRequestState.DRAFT : PullRequestState.OPEN,
                baseSha
            );

            pullRequests.put(number, pr);
            return pr;
        }

        void addCommit(int number, Commit commit) {
            PullRequest pr = getPullRequest(number);

            ensureActive(pr);

            pr.commits().add(commit);
            branches.put(pr.sourceBranch(), commit.sha());

            BranchProtection policy = protections.get(pr.targetBranch());

            if (policy != null && policy.dismissStaleReviews()) {
                pr.reviews().removeIf(
                    review -> !review.commitSha().equals(commit.sha())
                );
            }

            // CI results are attached to the exact commit being tested.
            pr.checks().clear();
        }

        void markReady(int number) {
            PullRequest pr = getPullRequest(number);

            if (pr.state() != PullRequestState.DRAFT) {
                throw new GovernanceException(
                    "Only draft Pull Requests can become ready"
                );
            }

            pr.setState(PullRequestState.OPEN);
        }

        void submitReview(
            int number,
            String reviewer,
            ReviewState state
        ) {
            PullRequest pr = getPullRequest(number);

            if (pr.state() != PullRequestState.OPEN) {
                throw new GovernanceException(
                    "Reviews require an open Pull Request"
                );
            }

            requireText(reviewer, "Reviewer");

            if (reviewer.equals(pr.author())) {
                throw new GovernanceException(
                    "Authors cannot review their own Pull Request"
                );
            }

            Commit latest = pr.latestCommit();

            if (latest == null) {
                throw new GovernanceException(
                    "A Pull Request must contain a commit before review"
                );
            }

            pr.reviews().add(
                new Review(
                    reviewer,
                    state,
                    latest.sha()
                )
            );
        }

        void setStatusCheck(
            int number,
            String name,
            CheckState state
        ) {
            PullRequest pr = getPullRequest(number);
            Commit latest = pr.latestCommit();

            if (latest == null) {
                throw new GovernanceException(
                    "Status checks require a commit"
                );
            }

            pr.checks().put(
                name,
                new StatusCheck(name, state, latest.sha())
            );
        }

        void addConversation(int number, String conversationId) {
            PullRequest pr = getPullRequest(number);
            pr.unresolvedConversations().add(conversationId);
        }

        void resolveConversation(int number, String conversationId) {
            PullRequest pr = getPullRequest(number);

            if (!pr.unresolvedConversations().remove(conversationId)) {
                throw new GovernanceException(
                    "Conversation is not unresolved: " + conversationId
                );
            }
        }

        void synchronizeBase(int number, String newBaseSha) {
            PullRequest pr = getPullRequest(number);
            requireText(newBaseSha, "Base SHA");

            pr.setCurrentBaseSha(newBaseSha);

            /*
             * A real merge engine compares the Git DAG. The model explicitly
             * represents the result while keeping governance independent from
             * the low-level Git implementation.
             */
            pr.setMergeConflicts(
                !newBaseSha.equals(pr.baseShaAtCreation())
            );

            BranchProtection policy = protections.get(pr.targetBranch());

            if (policy != null && policy.dismissStaleReviews()) {
                Commit latest = pr.latestCommit();

                if (latest != null) {
                    pr.reviews().removeIf(
                        review -> !review.commitSha().equals(latest.sha())
                    );
                }
            }
        }

        MergeDecision evaluateMerge(int number, String actor) {
            PullRequest pr = getPullRequest(number);
            BranchProtection policy = protections.get(pr.targetBranch());
            List<String> reasons = new ArrayList<>();

            requireText(actor, "Merge actor");

            if (policy == null) {
                return new MergeDecision(
                    false,
                    List.of("Target branch has no protection policy")
                );
            }

            if (policy.bypassUsers().contains(actor)) {
                return new MergeDecision(
                    true,
                    List.of("Configured governance bypass permits the merge")
                );
            }

            if (pr.state() != PullRequestState.OPEN) {
                reasons.add("Pull Request is not open");
            }

            Commit latest = pr.latestCommit();

            if (latest == null) {
                reasons.add("Pull Request has no commits");
            }

            if (pr.mergeConflicts()) {
                reasons.add("Merge conflicts remain unresolved");
            }

            if (!policy.allowedMergeStrategies().contains(
                pr.mergeStrategy()
            )) {
                reasons.add("Selected merge strategy is not permitted");
            }

            Set<String> currentApprovers = new HashSet<>();

            if (latest != null) {
                for (Review review : pr.reviews()) {
                    if (!review.commitSha().equals(latest.sha())) {
                        continue;
                    }

                    if (review.state() == ReviewState.APPROVED) {
                        currentApprovers.add(review.reviewer());
                    }

                    if (review.state() == ReviewState.CHANGES_REQUESTED) {
                        currentApprovers.remove(review.reviewer());
                    }
                }
            }

            if (currentApprovers.size() < policy.requiredReviews()) {
                reasons.add(
                    "Required approvals: "
                        + policy.requiredReviews()
                        + "; current approvals: "
                        + currentApprovers.size()
                );
            }

            if (latest != null) {
                for (String requiredCheck : policy.requiredChecks()) {
                    StatusCheck check = pr.checks().get(requiredCheck);

                    if (check == null) {
                        reasons.add(
                            "Missing required status check: "
                                + requiredCheck
                        );
                    } else if (!check.commitSha().equals(latest.sha())) {
                        reasons.add(
                            "Stale required status check: "
                                + requiredCheck
                        );
                    } else if (check.state() != CheckState.PASSED) {
                        reasons.add(
                            "Required status check failed: "
                                + requiredCheck
                        );
                    }
                }
            }

            if (
                policy.requireConversationResolution()
                && !pr.unresolvedConversations().isEmpty()
            ) {
                reasons.add("Unresolved review conversations remain");
            }

            if (
                policy.requireLinearHistory()
                && pr.mergeStrategy() == MergeStrategy.MERGE_COMMIT
            ) {
                reasons.add(
                    "Merge commits violate linear-history policy"
                );
            }

            return new MergeDecision(
                reasons.isEmpty(),
                reasons
            );
        }

        void merge(int number, String actor) {
            MergeDecision decision = evaluateMerge(number, actor);

            if (!decision.allowed()) {
                throw new GovernanceException(
                    "Merge blocked: "
                        + String.join("; ", decision.reasons())
                );
            }

            PullRequest pr = getPullRequest(number);
            Commit latest = pr.latestCommit();

            if (latest == null) {
                throw new GovernanceException(
                    "Internal invariant violation: no latest commit"
                );
            }

            String resultSha =
                "merge-"
                    + pr.number()
                    + "-"
                    + latest.sha().substring(
                        0,
                        Math.min(8, latest.sha().length())
                    )
                    + "-"
                    + pr.mergeStrategy().name().toLowerCase();

            branches.put(pr.targetBranch(), resultSha);
            pr.setState(PullRequestState.MERGED);
        }

        void close(int number) {
            PullRequest pr = getPullRequest(number);

            if (pr.state() == PullRequestState.MERGED) {
                throw new GovernanceException(
                    "A merged Pull Request cannot be closed"
                );
            }

            pr.setState(PullRequestState.CLOSED);
        }

        void reopen(int number) {
            PullRequest pr = getPullRequest(number);

            if (pr.state() != PullRequestState.CLOSED) {
                throw new GovernanceException(
                    "Only closed Pull Requests can be reopened"
                );
            }

            pr.setState(PullRequestState.OPEN);
        }

        private PullRequest getPullRequest(int number) {
            PullRequest pr = pullRequests.get(number);

            if (pr == null) {
                throw new GovernanceException(
                    "Unknown Pull Request: " + number
                );
            }

            return pr;
        }

        private static void ensureActive(PullRequest pr) {
            if (
                pr.state() != PullRequestState.DRAFT
                && pr.state() != PullRequestState.OPEN
            ) {
                throw new GovernanceException(
                    "Pull Request is not active"
                );
            }
        }
    }

    static final class GovernanceException extends RuntimeException {
        GovernanceException(String message) {
            super(message);
        }
    }

    static String requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(
                field + " must not be blank"
            );
        }
        return value.trim();
    }

    static void printDecision(
        Repository repository,
        int number,
        String actor
    ) {
        MergeDecision decision =
            repository.evaluateMerge(number, actor);

        System.out.println(
            "PR #" + number + ": "
                + (decision.allowed() ? "MERGEABLE" : "BLOCKED")
        );

        decision.reasons().forEach(
            reason -> System.out.println("  - " + reason)
        );
    }

    public static void main(String[] args) {
        Repository repository =
            new Repository("payments-platform");

        repository.createBranch("main", "base-001");
        repository.createBranch(
            "feature/payment-controls",
            "base-001"
        );

        repository.protectBranch(
            new BranchProtection(
                "main",
                2,
                Set.of("unit-tests", "security-scan"),
                true,
                true,
                true,
                false,
                false,
                true,
                EnumSet.of(
                    MergeStrategy.SQUASH,
                    MergeStrategy.REBASE
                ),
                Set.of()
            )
        );

        PullRequest pr =
            repository.createPullRequest(
                "Strengthen payment controls",
                "feature/payment-controls",
                "main",
                "alice",
                true
            );

        repository.addCommit(
            pr.number(),
            new Commit(
                "commit-001",
                "Validate transaction limits",
                "alice"
            )
        );

        repository.markReady(pr.number());

        repository.submitReview(
            pr.number(),
            "bob",
            ReviewState.APPROVED
        );

        repository.submitReview(
            pr.number(),
            "carol",
            ReviewState.APPROVED
        );

        repository.setStatusCheck(
            pr.number(),
            "unit-tests",
            CheckState.PASSED
        );

        repository.setStatusCheck(
            pr.number(),
            "security-scan",
            CheckState.PASSED
        );

        repository.addConversation(
            pr.number(),
            "conversation-1"
        );

        printDecision(
            repository,
            pr.number(),
            "release-manager"
        );

        repository.resolveConversation(
            pr.number(),
            "conversation-1"
        );

        printDecision(
            repository,
            pr.number(),
            "release-manager"
        );

        repository.merge(
            pr.number(),
            "release-manager"
        );

        PullRequest auditPr =
            repository.createPullRequest(
                "Add audit persistence",
                "feature/payment-controls",
                "main",
                "diana",
                false
            );

        repository.addCommit(
            auditPr.number(),
            new Commit(
                "commit-002",
                "Create audit record model",
                "diana"
            )
        );

        repository.submitReview(
            auditPr.number(),
            "erin",
            ReviewState.APPROVED
        );

        repository.submitReview(
            auditPr.number(),
            "frank",
            ReviewState.APPROVED
        );

        repository.setStatusCheck(
            auditPr.number(),
            "unit-tests",
            CheckState.PASSED
        );

        repository.setStatusCheck(
            auditPr.number(),
            "security-scan",
            CheckState.PASSED
        );

        /*
         * Adding a new commit clears old evidence because the governance
         * policy requires reviews and checks for the current revision.
         */
        repository.addCommit(
            auditPr.number(),
            new Commit(
                "commit-003",
                "Handle persistence failures",
                "diana"
            )
        );

        printDecision(
            repository,
            auditPr.number(),
            "release-manager"
        );

        repository.submitReview(
            auditPr.number(),
            "erin",
            ReviewState.APPROVED
        );

        repository.submitReview(
            auditPr.number(),
            "frank",
            ReviewState.APPROVED
        );

        repository.setStatusCheck(
            auditPr.number(),
            "unit-tests",
            CheckState.PASSED
        );

        repository.setStatusCheck(
            auditPr.number(),
            "security-scan",
            CheckState.PASSED
        );

        repository.merge(
            auditPr.number(),
            "release-manager"
        );

        System.out.println(
            "Final audit PR state: "
                + auditPr.state()
        );
    }
}
