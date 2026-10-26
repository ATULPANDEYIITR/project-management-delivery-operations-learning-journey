import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class RepositoryGovernance {

    enum PullRequestState {
        DRAFT, OPEN, CLOSED, MERGED
    }

    enum ReviewState {
        COMMENTED, APPROVED, CHANGES_REQUESTED, DISMISSED
    }

    enum CheckState {
        PASSING, FAILING, PENDING
    }

    enum MergeStrategy {
        MERGE, SQUASH, REBASE
    }

    record Commit(
        String sha,
        String message,
        String author
    ) {}

    record StatusCheck(
        String name,
        CheckState state
    ) {}

    record ReviewComment(
        long id,
        String reviewer,
        String body,
        boolean resolved
    ) {}

    record Review(
        String reviewer,
        ReviewState state,
        String commitSha,
        Instant submittedAt
    ) {}

    record BranchProtectionPolicy(
        int requiredApprovals,
        Set<String> requiredChecks,
        boolean requireResolvedConversations,
        boolean restrictDirectPush,
        boolean restrictForcePush,
        boolean restrictDeletion,
        boolean requireLinearHistory,
        boolean allowAdministratorBypass
    ) {
        BranchProtectionPolicy {
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException(
                    "Required approvals cannot be negative."
                );
            }

            requiredChecks = Set.copyOf(requiredChecks);
        }
    }

    static final class GovernanceException extends RuntimeException {
        GovernanceException(String message) {
            super(message);
        }
    }

    static final class Branch {
        private final String name;
        private final boolean protectedBranch;
        private String headSha;
        private final List<Commit> commits = new ArrayList<>();

        Branch(
            String name,
            boolean protectedBranch,
            String headSha
        ) {
            requireText(name, "Branch name");
            requireText(headSha, "Branch head SHA");

            this.name = name;
            this.protectedBranch = protectedBranch;
            this.headSha = headSha;
        }

        String name() {
            return name;
        }

        boolean protectedBranch() {
            return protectedBranch;
        }

        String headSha() {
            return headSha;
        }

        List<Commit> commits() {
            return commits;
        }

        void updateHead(String sha) {
            requireText(sha, "Branch head SHA");
            headSha = sha;
        }
    }

    static final class PullRequest {
        private final int number;
        private final String author;
        private final String sourceBranch;
        private final String targetBranch;
        private final String title;

        private PullRequestState state;
        private boolean draft;
        private String baseShaAtOpen;

        private final List<Commit> commits = new ArrayList<>();
        private final List<Review> reviews = new ArrayList<>();
        private final List<ReviewComment> conversations =
            new ArrayList<>();
        private final Map<String, StatusCheck> checks =
            new HashMap<>();

        PullRequest(
            int number,
            String author,
            String sourceBranch,
            String targetBranch,
            String title,
            boolean draft,
            String baseShaAtOpen
        ) {
            if (number <= 0) {
                throw new GovernanceException(
                    "Pull Request number must be positive."
                );
            }

            requireText(author, "Author");
            requireText(sourceBranch, "Source branch");
            requireText(targetBranch, "Target branch");
            requireText(title, "Title");

            this.number = number;
            this.author = author;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.title = title;
            this.draft = draft;
            this.state = draft
                ? PullRequestState.DRAFT
                : PullRequestState.OPEN;
            this.baseShaAtOpen = baseShaAtOpen;
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

        String title() {
            return title;
        }

        PullRequestState state() {
            return state;
        }

        void publish() {
            if (!draft) {
                return;
            }

            draft = false;
            state = PullRequestState.OPEN;
        }

        boolean isDraft() {
            return draft;
        }

        String baseShaAtOpen() {
            return baseShaAtOpen;
        }

        void synchronizeBase(String sha) {
            requireText(sha, "Base SHA");
            baseShaAtOpen = sha;

            // A new base means previous approvals may no longer describe
            // the exact change set being evaluated.
            for (int i = 0; i < reviews.size(); i++) {
                Review review = reviews.get(i);

                if (review.state() == ReviewState.APPROVED) {
                    reviews.set(
                        i,
                        new Review(
                            review.reviewer(),
                            ReviewState.DISMISSED,
                            review.commitSha(),
                            review.submittedAt()
                        )
                    );
                }
            }
        }

        List<Commit> commits() {
            return commits;
        }

        List<Review> reviews() {
            return reviews;
        }

        List<ReviewComment> conversations() {
            return conversations;
        }

        Map<String, StatusCheck> checks() {
            return checks;
        }

        void setState(PullRequestState state) {
            this.state = state;
        }
    }

    static final class Repository {
        private final String name;
        private final Map<String, Branch> branches = new HashMap<>();
        private final Set<String> eligibleReviewers = new HashSet<>();
        private final Map<Integer, PullRequest> pullRequests =
            new HashMap<>();
        private final BranchProtectionPolicy protection;

        Repository(
            String name,
            BranchProtectionPolicy protection
        ) {
            requireText(name, "Repository name");
            this.name = name;
            this.protection = protection;
        }

        void addBranch(Branch branch) {
            if (branches.putIfAbsent(branch.name(), branch) != null) {
                throw new GovernanceException(
                    "Branch already exists."
                );
            }
        }

        void addReviewer(String reviewer) {
            requireText(reviewer, "Reviewer");
            eligibleReviewers.add(reviewer);
        }

        PullRequest createPullRequest(
            int number,
            String author,
            String source,
            String target,
            String title,
            boolean draft
        ) {
            if (!branches.containsKey(source) ||
                !branches.containsKey(target)) {
                throw new GovernanceException(
                    "Both source and target branches must exist."
                );
            }

            if (source.equals(target)) {
                throw new GovernanceException(
                    "Source and target branches must differ."
                );
            }

            if (pullRequests.containsKey(number)) {
                throw new GovernanceException(
                    "Pull Request already exists."
                );
            }

            PullRequest pr = new PullRequest(
                number,
                author,
                source,
                target,
                title,
                draft,
                branches.get(target).headSha()
            );

            pullRequests.put(number, pr);
            return pr;
        }

        void addCommit(
            PullRequest pr,
            Commit commit
        ) {
            if (pr.state() != PullRequestState.OPEN &&
                pr.state() != PullRequestState.DRAFT) {
                throw new GovernanceException(
                    "Commits cannot be added to this Pull Request."
                );
            }

            if (pr.commits().stream()
                .anyMatch(existing ->
                    existing.sha().equals(commit.sha()))) {
                throw new GovernanceException(
                    "Duplicate commit."
                );
            }

            pr.commits().add(commit);

            Branch source = branches.get(pr.sourceBranch());
            source.commits().add(commit);
            source.updateHead(commit.sha());
        }

        void submitReview(
            PullRequest pr,
            String reviewer,
            ReviewState state,
            String commitSha
        ) {
            if (pr.state() != PullRequestState.OPEN) {
                throw new GovernanceException(
                    "Reviews require an open Pull Request."
                );
            }

            if (pr.author().equals(reviewer)) {
                throw new GovernanceException(
                    "Self-approval is forbidden."
                );
            }

            if (!eligibleReviewers.contains(reviewer)) {
                throw new GovernanceException(
                    "Reviewer is not eligible."
                );
            }

            pr.reviews().add(
                new Review(
                    reviewer,
                    state,
                    commitSha,
                    Instant.now()
                )
            );
        }

        void addConversation(
            PullRequest pr,
            String reviewer,
            String body
        ) {
            long id = pr.conversations().size() + 1L;

            pr.conversations().add(
                new ReviewComment(
                    id,
                    reviewer,
                    body,
                    false
                )
            );
        }

        void resolveConversation(
            PullRequest pr,
            long id
        ) {
            for (int i = 0; i < pr.conversations().size(); i++) {
                ReviewComment comment = pr.conversations().get(i);

                if (comment.id() == id) {
                    pr.conversations().set(
                        i,
                        new ReviewComment(
                            comment.id(),
                            comment.reviewer(),
                            comment.body(),
                            true
                        )
                    );
                    return;
                }
            }

            throw new GovernanceException(
                "Conversation does not exist."
            );
        }

        void setStatus(
            PullRequest pr,
            String name,
            CheckState state
        ) {
            pr.checks().put(
                name,
                new StatusCheck(name, state)
            );
        }

        MergeDecision evaluate(PullRequest pr) {
            List<String> failures = new ArrayList<>();

            if (pr.state() != PullRequestState.OPEN) {
                failures.add("Pull Request is not open.");
            }

            if (pr.isDraft()) {
                failures.add("Pull Request is a draft.");
            }

            if (pr.commits().isEmpty()) {
                failures.add("Pull Request has no commits.");
            }

            Set<String> approvals = new HashSet<>();

            for (Review review : pr.reviews()) {
                if (review.state() == ReviewState.CHANGES_REQUESTED) {
                    failures.add(
                        review.reviewer() +
                        " requested changes."
                    );
                }

                if (review.state() == ReviewState.APPROVED) {
                    approvals.add(review.reviewer());
                }
            }

            if (approvals.size() <
                protection.requiredApprovals()) {
                failures.add(
                    "Required approval count is not satisfied."
                );
            }

            for (String required : protection.requiredChecks()) {
                StatusCheck check = pr.checks().get(required);

                if (check == null) {
                    failures.add(
                        "Required status check '" +
                        required +
                        "' is missing."
                    );
                } else if (check.state() != CheckState.PASSING) {
                    failures.add(
                        "Required status check '" +
                        required +
                        "' is not passing."
                    );
                }
            }

            if (protection.requireResolvedConversations()) {
                boolean unresolved = pr.conversations()
                    .stream()
                    .anyMatch(comment -> !comment.resolved());

                if (unresolved) {
                    failures.add(
                        "Unresolved review conversations remain."
                    );
                }
            }

            Branch target = branches.get(pr.targetBranch());

            if (!target.headSha().equals(pr.baseShaAtOpen())) {
                failures.add(
                    "Pull Request base branch is out of date."
                );
            }

            return new MergeDecision(
                failures.isEmpty(),
                List.copyOf(failures)
            );
        }

        void merge(
            PullRequest pr,
            MergeStrategy strategy
        ) {
            MergeDecision decision = evaluate(pr);

            if (!decision.eligible()) {
                throw new GovernanceException(
                    String.join("; ", decision.reasons())
                );
            }

            String mergeSha =
                strategy.name().toLowerCase() +
                "-pr-" +
                pr.number();

            Branch target = branches.get(pr.targetBranch());

            target.commits().add(
                new Commit(
                    mergeSha,
                    "Integrate PR #" + pr.number() +
                        ": " + pr.title(),
                    pr.author()
                )
            );

            target.updateHead(mergeSha);
            pr.setState(PullRequestState.MERGED);
        }
    }

    record MergeDecision(
        boolean eligible,
        List<String> reasons
    ) {}

    private static void requireText(
        String value,
        String field
    ) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(
                field + " cannot be empty."
            );
        }
    }

    public static void main(String[] args) {
        BranchProtectionPolicy policy =
            new BranchProtectionPolicy(
                2,
                Set.of("unit-tests", "security-scan"),
                true,
                true,
                true,
                true,
                true,
                false
            );

        Repository repository =
            new Repository("payments-service", policy);

        repository.addBranch(
            new Branch(
                "main",
                true,
                "main-base-001"
            )
        );

        repository.addBranch(
            new Branch(
                "feature/refund-validation",
                false,
                "feature-base-001"
            )
        );

        repository.addReviewer("alice");
        repository.addReviewer("bob");
        repository.addReviewer("carol");

        PullRequest pr =
            repository.createPullRequest(
                501,
                "developer",
                "feature/refund-validation",
                "main",
                "Validate refund requests",
                true
            );

        repository.addCommit(
            pr,
            new Commit(
                "abcdef123456",
                "Add refund validation",
                "developer"
            )
        );

        repository.addConversation(
            pr,
            "alice",
            "Please validate the zero-value boundary."
        );

        repository.setStatus(
            pr,
            "unit-tests",
            CheckState.PASSING
        );

        repository.setStatus(
            pr,
            "security-scan",
            CheckState.PASSING
        );

        MergeDecision before =
            repository.evaluate(pr);

        System.out.println(
            "Before publishing and approvals: " +
            before.eligible()
        );

        pr.publish();

        repository.submitReview(
            pr,
            "alice",
            ReviewState.APPROVED,
            "abcdef123456"
        );

        repository.submitReview(
            pr,
            "bob",
            ReviewState.APPROVED,
            "abcdef123456"
        );

        repository.resolveConversation(pr, 1);

        MergeDecision after =
            repository.evaluate(pr);

        System.out.println(
            "After review policy evaluation: " +
            after.eligible()
        );

        if (after.eligible()) {
            repository.merge(
                pr,
                MergeStrategy.SQUASH
            );
        }

        System.out.println(
            "Final Pull Request state: " +
            pr.state()
        );

        try {
            pr.setState(PullRequestState.OPEN);
            throw new GovernanceException(
                "Direct state manipulation should not be permitted in production."
            );
        } catch (GovernanceException exception) {
            System.out.println(
                "Governance warning: " +
                exception.getMessage()
            );
        }
    }
}
