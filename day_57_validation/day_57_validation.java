import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class ProjectGovernanceDemo {

    enum WorkItemState {
        DRAFT, OPEN, IN_REVIEW, APPROVED,
        CHANGES_REQUESTED, MERGED, CLOSED
    }

    enum ReviewState {
        COMMENTED, APPROVED, CHANGES_REQUESTED, DISMISSED
    }

    enum CheckState {
        PENDING, PASSED, FAILED
    }

    record User(String id, String name, Role role) {}

    enum Role {
        DEVELOPER, REVIEWER, PROJECT_MANAGER, MAINTAINER
    }

    record Commit(
        String id,
        String message,
        String authorId,
        int revision,
        Instant createdAt
    ) {}

    record ReviewComment(
        String id,
        String text,
        boolean resolved
    ) {}

    record Review(
        String reviewerId,
        ReviewState state,
        int revisionReviewed,
        List<ReviewComment> comments,
        Instant submittedAt
    ) {}

    record StatusCheck(
        String name,
        CheckState state
    ) {}

    record Branch(
        String name,
        boolean protectedBranch,
        List<String> commitIds
    ) {}

    static final class GovernanceException extends Exception {
        GovernanceException(String message) {
            super(message);
        }
    }

    static final class PullRequest {
        private final int number;
        private final String title;
        private final String authorId;
        private final String sourceBranch;
        private final String targetBranch;

        private WorkItemState state;
        private boolean draft;
        private boolean conflicted;
        private boolean baseSynchronized = true;
        private int revision = 0;
        private int openConversations = 0;

        private final List<Commit> commits = new ArrayList<>();
        private final List<Review> reviews = new ArrayList<>();
        private final Map<String, StatusCheck> checks = new HashMap<>();

        PullRequest(
            int number,
            String title,
            String authorId,
            String sourceBranch,
            String targetBranch,
            boolean draft
        ) {
            this.number = number;
            this.title = title;
            this.authorId = authorId;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.draft = draft;
            this.state = draft
                ? WorkItemState.DRAFT
                : WorkItemState.OPEN;
        }

        void addCommit(
            String id,
            String message,
            String authorId
        ) throws GovernanceException {
            if (state == WorkItemState.MERGED ||
                state == WorkItemState.CLOSED) {
                throw new GovernanceException(
                    "A completed Pull Request cannot receive commits."
                );
            }

            if (!this.authorId.equals(authorId)) {
                throw new GovernanceException(
                    "Commit author does not match Pull Request author."
                );
            }

            if (message == null || message.isBlank()) {
                throw new GovernanceException(
                    "Commit message cannot be empty."
                );
            }

            revision++;

            commits.add(new Commit(
                id,
                message.trim(),
                authorId,
                revision,
                Instant.now()
            ));

            // Every revision represents a new reviewable state.
            // Older approvals remain stored but are no longer current.
            state = WorkItemState.OPEN;
        }

        void markReady() throws GovernanceException {
            if (draft) {
                throw new GovernanceException(
                    "Draft Pull Requests cannot be submitted for final review."
                );
            }

            if (commits.isEmpty()) {
                throw new GovernanceException(
                    "At least one commit is required."
                );
            }

            state = WorkItemState.IN_REVIEW;
        }

        void submitReview(
            String reviewerId,
            ReviewState reviewState,
            List<ReviewComment> comments
        ) throws GovernanceException {
            if (reviewerId.equals(authorId)) {
                throw new GovernanceException(
                    "Self-approval is prohibited."
                );
            }

            reviews.add(new Review(
                reviewerId,
                reviewState,
                revision,
                List.copyOf(comments),
                Instant.now()
            ));

            if (reviewState == ReviewState.CHANGES_REQUESTED) {
                state = WorkItemState.CHANGES_REQUESTED;
            } else if (reviewState == ReviewState.APPROVED) {
                state = WorkItemState.APPROVED;
            }
        }

        void addStatusCheck(String name, CheckState state) {
            checks.put(name, new StatusCheck(name, state));
        }

        void openConversation() {
            openConversations++;
        }

        void resolveConversation() throws GovernanceException {
            if (openConversations <= 0) {
                throw new GovernanceException(
                    "No open review conversation exists."
                );
            }
            openConversations--;
        }

        void setConflict(boolean conflicted) {
            this.conflicted = conflicted;
            this.baseSynchronized = !conflicted;
        }

        int revision() {
            return revision;
        }

        String authorId() {
            return authorId;
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        Map<String, StatusCheck> checks() {
            return Map.copyOf(checks);
        }

        int openConversations() {
            return openConversations;
        }

        boolean isDraft() {
            return draft;
        }

        boolean isConflicted() {
            return conflicted;
        }

        boolean isBaseSynchronized() {
            return baseSynchronized;
        }

        String targetBranch() {
            return targetBranch;
        }

        String title() {
            return title;
        }

        int number() {
            return number;
        }
    }

    record ReviewPolicy(
        int requiredApprovals,
        Set<String> requiredChecks,
        boolean requireResolvedConversations
    ) {
        ReviewPolicy {
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException(
                    "Required approvals cannot be negative."
                );
            }
            requiredChecks = Set.copyOf(requiredChecks);
        }
    }

    record EligibilityResult(
        boolean eligible,
        List<String> reasons
    ) {}

    static final class MergeEligibilityService {
        private final Map<String, User> users;
        private final ReviewPolicy policy;

        MergeEligibilityService(
            List<User> users,
            ReviewPolicy policy
        ) {
            this.users = new HashMap<>();

            for (User user : users) {
                this.users.put(user.id(), user);
            }

            this.policy = policy;
        }

        private boolean eligibleReviewer(
            PullRequest pr,
            String reviewerId
        ) {
            if (reviewerId.equals(pr.authorId())) {
                return false;
            }

            User user = users.get(reviewerId);

            if (user == null) {
                return false;
            }

            return user.role() == Role.REVIEWER ||
                   user.role() == Role.PROJECT_MANAGER ||
                   user.role() == Role.MAINTAINER;
        }

        EligibilityResult evaluate(
            PullRequest pr,
            Branch target
        ) {
            List<String> reasons = new ArrayList<>();

            if (pr.isDraft()) {
                reasons.add("Pull Request is still a draft.");
            }

            if (pr.isConflicted()) {
                reasons.add("Merge conflicts exist.");
            }

            if (!pr.isBaseSynchronized()) {
                reasons.add("Base branch is not synchronized.");
            }

            Set<String> currentApprovers = new HashSet<>();

            for (Review review : pr.reviews()) {
                if (review.state() == ReviewState.APPROVED &&
                    review.revisionReviewed() == pr.revision() &&
                    eligibleReviewer(pr, review.reviewerId())) {
                    currentApprovers.add(review.reviewerId());
                }
            }

            if (currentApprovers.size() < policy.requiredApprovals()) {
                reasons.add(
                    "The required number of current eligible approvals is missing."
                );
            }

            for (String checkName : policy.requiredChecks()) {
                StatusCheck check = pr.checks().get(checkName);

                if (check == null) {
                    reasons.add(
                        "Required check is missing: " + checkName
                    );
                } else if (check.state() != CheckState.PASSED) {
                    reasons.add(
                        "Required check has not passed: " + checkName
                    );
                }
            }

            if (policy.requireResolvedConversations() &&
                pr.openConversations() > 0) {
                reasons.add("Unresolved review conversations remain.");
            }

            if (target.protectedBranch() &&
                !target.name().equals(pr.targetBranch())) {
                reasons.add("Target branch does not match protected branch.");
            }

            return new EligibilityResult(
                reasons.isEmpty(),
                List.copyOf(reasons)
            );
        }
    }

    static final class ProjectWorkflowService {
        private final MergeEligibilityService eligibilityService;

        ProjectWorkflowService(
            MergeEligibilityService eligibilityService
        ) {
            this.eligibilityService = eligibilityService;
        }

        void merge(
            PullRequest pr,
            Branch target
        ) throws GovernanceException {
            EligibilityResult result =
                eligibilityService.evaluate(pr, target);

            if (!result.eligible()) {
                throw new GovernanceException(
                    String.join(" ", result.reasons())
                );
            }

            for (Commit commit : List.copyOf(pr.commits)) {
                target.commitIds().add(commit.id());
            }
        }
    }

    public static void main(String[] args) {
        try {
            List<User> users = List.of(
                new User("u1", "Project Manager", Role.PROJECT_MANAGER),
                new User("u2", "Architecture Reviewer", Role.REVIEWER),
                new User("u3", "Quality Reviewer", Role.REVIEWER),
                new User("u4", "Developer", Role.DEVELOPER)
            );

            ReviewPolicy policy = new ReviewPolicy(
                2,
                Set.of(
                    "scope-validation",
                    "security-validation",
                    "quality-gate"
                ),
                true
            );

            Branch main = new Branch(
                "main",
                true,
                new ArrayList<>(List.of("base-001"))
            );

            PullRequest pr = new PullRequest(
                900,
                "Introduce enterprise project-risk workflow",
                "u4",
                "feature/risk-workflow",
                "main",
                false
            );

            pr.addCommit(
                "commit-001",
                "Implement risk-control workflow",
                "u4"
            );

            pr.markReady();

            pr.addStatusCheck(
                "scope-validation",
                CheckState.PASSED
            );
            pr.addStatusCheck(
                "security-validation",
                CheckState.PASSED
            );
            pr.addStatusCheck(
                "quality-gate",
                CheckState.PASSED
            );

            pr.submitReview(
                "u2",
                ReviewState.APPROVED,
                List.of(
                    new ReviewComment(
                        "comment-1",
                        "Risk calculation is traceable.",
                        true
                    )
                )
            );

            pr.submitReview(
                "u3",
                ReviewState.APPROVED,
                List.of(
                    new ReviewComment(
                        "comment-2",
                        "Validation evidence is complete.",
                        true
                    )
                )
            );

            MergeEligibilityService evaluator =
                new MergeEligibilityService(users, policy);

            EligibilityResult result =
                evaluator.evaluate(pr, main);

            System.out.println("Enterprise Project Governance");
            System.out.println("==============================");
            System.out.println(
                "PR #" + pr.number() + ": " + pr.title()
            );
            System.out.println(
                "Eligible: " + result.eligible()
            );

            for (String reason : result.reasons()) {
                System.out.println("- " + reason);
            }

            if (result.eligible()) {
                ProjectWorkflowService workflow =
                    new ProjectWorkflowService(evaluator);

                workflow.merge(pr, main);
                System.out.println("Merge executed successfully.");
            }

            // New revision invalidates the previous review decisions.
            PullRequest revisedPr = new PullRequest(
                901,
                "Update project cost-control policy",
                "u4",
                "feature/cost-policy",
                "main",
                false
            );

            revisedPr.addCommit(
                "commit-101",
                "Add cost threshold",
                "u4"
            );
            revisedPr.markReady();

            revisedPr.addStatusCheck(
                "scope-validation",
                CheckState.PASSED
            );
            revisedPr.addStatusCheck(
                "security-validation",
                CheckState.PASSED
            );
            revisedPr.addStatusCheck(
                "quality-gate",
                CheckState.PASSED
            );

            revisedPr.submitReview(
                "u2",
                ReviewState.APPROVED,
                List.of()
            );
            revisedPr.submitReview(
                "u3",
                ReviewState.APPROVED,
                List.of()
            );

            revisedPr.addCommit(
                "commit-102",
                "Fix cost boundary condition",
                "u4"
            );

            result = evaluator.evaluate(revisedPr, main);

            System.out.println("\nStale Approval Scenario");
            System.out.println("=======================");
            System.out.println(
                "Eligible: " + result.eligible()
            );

            for (String reason : result.reasons()) {
                System.out.println("- " + reason);
            }

        } catch (GovernanceException | IllegalArgumentException ex) {
            System.err.println(
                "Workflow rejected: " + ex.getMessage()
            );
            System.exit(1);
        }
    }
}
