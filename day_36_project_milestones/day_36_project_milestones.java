import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

public class ProjectMilestoneGovernance {

    enum MilestoneStatus {
        PLANNED,
        ACTIVE,
        COMPLETED,
        BLOCKED,
        CANCELLED
    }

    enum ReviewState {
        APPROVED,
        CHANGES_REQUESTED,
        COMMENTED
    }

    enum ProjectEventType {
        PROJECT_STARTED,
        REQUIREMENT_APPROVED,
        DESIGN_COMPLETED,
        PULL_REQUEST_OPENED,
        CODE_REVIEW_COMPLETED,
        APPROVAL_GRANTED,
        STATUS_CHECK_FAILED,
        STATUS_CHECK_PASSED,
        MERGED,
        RELEASED,
        MILESTONE_COMPLETED,
        MILESTONE_BLOCKED
    }

    record ProjectEvent(
        long id,
        ProjectEventType type,
        String title,
        String actor,
        String milestoneId,
        Instant occurredAt,
        String details
    ) {
        public ProjectEvent {
            Objects.requireNonNull(type);
            Objects.requireNonNull(title);
            Objects.requireNonNull(actor);
            Objects.requireNonNull(occurredAt);
        }
    }

    record BranchProtectionPolicy(
        String branch,
        int requiredApprovals,
        Set<String> requiredStatusChecks,
        boolean requireConversationResolution,
        boolean restrictDirectPushes,
        boolean allowForcePush,
        boolean allowDeletion,
        boolean requireLinearHistory,
        boolean dismissStaleApprovals
    ) {
        public BranchProtectionPolicy {
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException(
                    "Required approvals cannot be negative."
                );
            }

            requiredStatusChecks =
                Set.copyOf(requiredStatusChecks);
        }
    }

    static final class Milestone {
        private final String id;
        private final String name;
        private final String description;
        private final LocalDate targetDate;
        private final int importance;
        private final Set<String> dependencies;
        private MilestoneStatus status;
        private Instant completedAt;

        Milestone(
            String id,
            String name,
            String description,
            LocalDate targetDate,
            int importance,
            Set<String> dependencies
        ) {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException(
                    "Milestone ID is required."
                );
            }

            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Milestone name is required."
                );
            }

            if (importance < 1 || importance > 5) {
                throw new IllegalArgumentException(
                    "Importance must be between 1 and 5."
                );
            }

            this.id = id;
            this.name = name;
            this.description = description;
            this.targetDate = Objects.requireNonNull(targetDate);
            this.importance = importance;
            this.dependencies = new HashSet<>(dependencies);
            this.status = MilestoneStatus.PLANNED;
        }

        String id() {
            return id;
        }

        String name() {
            return name;
        }

        LocalDate targetDate() {
            return targetDate;
        }

        int importance() {
            return importance;
        }

        MilestoneStatus status() {
            return status;
        }

        Set<String> dependencies() {
            return Set.copyOf(dependencies);
        }

        void activate() {
            if (
                status != MilestoneStatus.PLANNED &&
                status != MilestoneStatus.BLOCKED
            ) {
                throw new IllegalStateException(
                    "Invalid milestone activation from " + status
                );
            }

            status = MilestoneStatus.ACTIVE;
        }

        void complete() {
            if (status == MilestoneStatus.CANCELLED) {
                throw new IllegalStateException(
                    "Cancelled milestone cannot be completed."
                );
            }

            status = MilestoneStatus.COMPLETED;
            completedAt = Instant.now();
        }

        void block() {
            if (status == MilestoneStatus.COMPLETED) {
                throw new IllegalStateException(
                    "Completed milestone cannot be blocked."
                );
            }

            status = MilestoneStatus.BLOCKED;
        }
    }

    static final class Review {
        private final String reviewer;
        private ReviewState state;
        private final int commentCount;
        private final int resolvedCommentCount;

        Review(
            String reviewer,
            ReviewState state,
            int commentCount,
            int resolvedCommentCount
        ) {
            if (commentCount < 0 || resolvedCommentCount < 0) {
                throw new IllegalArgumentException(
                    "Review comment counts cannot be negative."
                );
            }

            if (resolvedCommentCount > commentCount) {
                throw new IllegalArgumentException(
                    "Resolved comments cannot exceed total comments."
                );
            }

            this.reviewer = Objects.requireNonNull(reviewer);
            this.state = Objects.requireNonNull(state);
            this.commentCount = commentCount;
            this.resolvedCommentCount = resolvedCommentCount;
        }

        String reviewer() {
            return reviewer;
        }

        ReviewState state() {
            return state;
        }

        int unresolvedComments() {
            return commentCount - resolvedCommentCount;
        }

        boolean isApproval() {
            return state == ReviewState.APPROVED &&
                unresolvedComments() == 0;
        }

        void dismissApproval() {
            if (state == ReviewState.APPROVED) {
                state = ReviewState.COMMENTED;
            }
        }
    }

    static final class PullRequest {
        private final int number;
        private final String sourceBranch;
        private final String targetBranch;
        private final String milestoneId;
        private final List<String> commits;
        private final List<Review> reviews = new ArrayList<>();
        private final Map<String, Boolean> statusChecks =
            new HashMap<>();

        private boolean draft;
        private boolean conflicted;
        private boolean merged;

        PullRequest(
            int number,
            String sourceBranch,
            String targetBranch,
            String milestoneId,
            List<String> commits,
            boolean draft
        ) {
            if (sourceBranch.equals(targetBranch)) {
                throw new IllegalArgumentException(
                    "Source and target branches must differ."
                );
            }

            if (commits == null || commits.isEmpty()) {
                throw new IllegalArgumentException(
                    "Pull Request requires at least one commit."
                );
            }

            this.number = number;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.milestoneId = milestoneId;
            this.commits = new ArrayList<>(commits);
            this.draft = draft;
        }

        int number() {
            return number;
        }

        String targetBranch() {
            return targetBranch;
        }

        String milestoneId() {
            return milestoneId;
        }

        boolean isDraft() {
            return draft;
        }

        boolean isMerged() {
            return merged;
        }

        boolean hasConflicts() {
            return conflicted;
        }

        void markReady() {
            if (merged) {
                throw new IllegalStateException(
                    "Merged Pull Request cannot become ready."
                );
            }

            draft = false;
        }

        void setConflicted(boolean conflicted) {
            this.conflicted = conflicted;
        }

        void addReview(Review review) {
            reviews.add(review);
        }

        void setStatusCheck(String name, boolean passed) {
            statusChecks.put(name, passed);
        }

        boolean statusCheckPassed(String name) {
            return statusChecks.getOrDefault(name, false);
        }

        int approvalCount() {
            Set<String> approvers = new HashSet<>();

            for (Review review : reviews) {
                if (review.isApproval()) {
                    approvers.add(review.reviewer());
                }
            }

            return approvers.size();
        }

        boolean hasChangesRequested() {
            return reviews.stream()
                .anyMatch(
                    review ->
                        review.state() == ReviewState.CHANGES_REQUESTED
                );
        }

        int unresolvedComments() {
            return reviews.stream()
                .mapToInt(Review::unresolvedComments)
                .sum();
        }

        void merge() {
            if (merged) {
                throw new IllegalStateException(
                    "Pull Request is already merged."
                );
            }

            merged = true;
        }

        void synchronize(String commit, boolean dismissStaleApprovals) {
            if (merged) {
                throw new IllegalStateException(
                    "Merged Pull Request cannot be synchronized."
                );
            }

            if (commit == null || commit.isBlank()) {
                throw new IllegalArgumentException(
                    "Synchronization requires a commit."
                );
            }

            commits.add(commit);

            if (dismissStaleApprovals) {
                reviews.forEach(Review::dismissApproval);
            }
        }
    }

    static final class MergeDecision {
        private final boolean eligible;
        private final List<String> reasons;

        MergeDecision(boolean eligible, List<String> reasons) {
            this.eligible = eligible;
            this.reasons = List.copyOf(reasons);
        }

        boolean eligible() {
            return eligible;
        }

        List<String> reasons() {
            return reasons;
        }

        @Override
        public String toString() {
            return "MergeDecision{" +
                "eligible=" + eligible +
                ", reasons=" + reasons +
                '}';
        }
    }

    static final class RepositoryGovernanceService {
        private final Map<String, Milestone> milestones =
            new HashMap<>();

        private final Map<Integer, PullRequest> pullRequests =
            new HashMap<>();

        private final Map<String, BranchProtectionPolicy>
            branchPolicies = new HashMap<>();

        private final List<ProjectEvent> events =
            new ArrayList<>();

        private long nextEventId = 1;

        void addMilestone(Milestone milestone) {
            if (milestones.containsKey(milestone.id())) {
                throw new IllegalArgumentException(
                    "Duplicate milestone: " + milestone.id()
                );
            }

            for (String dependency : milestone.dependencies()) {
                if (!milestones.containsKey(dependency)) {
                    throw new IllegalArgumentException(
                        "Unknown dependency: " + dependency
                    );
                }
            }

            milestones.put(milestone.id(), milestone);
        }

        void configureBranchProtection(
            BranchProtectionPolicy policy
        ) {
            branchPolicies.put(policy.branch(), policy);
        }

        void recordEvent(
            ProjectEventType type,
            String title,
            String actor,
            String milestoneId,
            String details
        ) {
            if (
                milestoneId != null &&
                !milestones.containsKey(milestoneId)
            ) {
                throw new IllegalArgumentException(
                    "Unknown milestone: " + milestoneId
                );
            }

            events.add(
                new ProjectEvent(
                    nextEventId++,
                    type,
                    title,
                    actor,
                    milestoneId,
                    Instant.now(),
                    details
                )
            );
        }

        void activateMilestone(String milestoneId) {
            Milestone milestone = milestone(milestoneId);

            for (String dependency : milestone.dependencies()) {
                if (
                    milestone(dependency).status() !=
                    MilestoneStatus.COMPLETED
                ) {
                    throw new IllegalStateException(
                        "Dependency " + dependency +
                        " is not completed."
                    );
                }
            }

            milestone.activate();
        }

        void completeMilestone(
            String milestoneId,
            String actor,
            String reason
        ) {
            Milestone milestone = milestone(milestoneId);

            boolean unfinishedPullRequest =
                pullRequests.values().stream()
                    .anyMatch(
                        pr ->
                            pr.milestoneId().equals(milestoneId) &&
                            !pr.isMerged()
                    );

            if (unfinishedPullRequest) {
                throw new IllegalStateException(
                    "Milestone still has an unmerged Pull Request."
                );
            }

            milestone.complete();

            recordEvent(
                ProjectEventType.MILESTONE_COMPLETED,
                "Milestone completed: " + milestone.name(),
                actor,
                milestoneId,
                reason
            );
        }

        void openPullRequest(
            PullRequest pullRequest,
            String actor
        ) {
            if (pullRequests.containsKey(pullRequest.number())) {
                throw new IllegalArgumentException(
                    "Duplicate Pull Request."
                );
            }

            if (
                !milestones.containsKey(
                    pullRequest.milestoneId()
                )
            ) {
                throw new IllegalArgumentException(
                    "Pull Request references an unknown milestone."
                );
            }

            pullRequests.put(
                pullRequest.number(),
                pullRequest
            );

            recordEvent(
                ProjectEventType.PULL_REQUEST_OPENED,
                "Pull Request #" +
                    pullRequest.number() +
                    " opened",
                actor,
                pullRequest.milestoneId(),
                "Source=" + pullRequest.number()
            );
        }

        void submitReview(
            int pullRequestNumber,
            Review review
        ) {
            PullRequest pullRequest =
                pullRequest(pullRequestNumber);

            pullRequest.addReview(review);

            recordEvent(
                review.isApproval()
                    ? ProjectEventType.APPROVAL_GRANTED
                    : ProjectEventType.CODE_REVIEW_COMPLETED,
                "Review submitted for Pull Request #" +
                    pullRequestNumber,
                review.reviewer(),
                pullRequest.milestoneId(),
                "State=" + review.state()
            );
        }

        void updateStatusCheck(
            int pullRequestNumber,
            String checkName,
            boolean passed,
            String actor
        ) {
            PullRequest pullRequest =
                pullRequest(pullRequestNumber);

            pullRequest.setStatusCheck(checkName, passed);

            recordEvent(
                passed
                    ? ProjectEventType.STATUS_CHECK_PASSED
                    : ProjectEventType.STATUS_CHECK_FAILED,
                checkName +
                    (passed ? " passed" : " failed"),
                actor,
                pullRequest.milestoneId(),
                ""
            );
        }

        MergeDecision evaluateMerge(int pullRequestNumber) {
            PullRequest pullRequest =
                pullRequest(pullRequestNumber);

            BranchProtectionPolicy policy =
                branchPolicies.get(pullRequest.targetBranch());

            List<String> failures = new ArrayList<>();

            if (policy == null) {
                failures.add(
                    "Target branch has no branch protection policy."
                );
            }

            if (pullRequest.isDraft()) {
                failures.add(
                    "Pull Request is still a draft."
                );
            }

            if (pullRequest.hasConflicts()) {
                failures.add(
                    "Pull Request has merge conflicts."
                );
            }

            if (pullRequest.hasChangesRequested()) {
                failures.add(
                    "A review has requested changes."
                );
            }

            if (policy != null) {
                if (
                    pullRequest.approvalCount() <
                    policy.requiredApprovals()
                ) {
                    failures.add(
                        "Required approvals: " +
                        policy.requiredApprovals() +
                        ", actual approvals: " +
                        pullRequest.approvalCount()
                    );
                }

                for (
                    String check :
                    policy.requiredStatusChecks()
                ) {
                    if (!pullRequest.statusCheckPassed(check)) {
                        failures.add(
                            "Required status check failed or missing: " +
                            check
                        );
                    }
                }

                if (
                    policy.requireConversationResolution() &&
                    pullRequest.unresolvedComments() > 0
                ) {
                    failures.add(
                        "Review conversations remain unresolved."
                    );
                }
            }

            return new MergeDecision(
                failures.isEmpty(),
                failures
            );
        }

        void merge(
            int pullRequestNumber,
            String actor
        ) {
            PullRequest pullRequest =
                pullRequest(pullRequestNumber);

            MergeDecision decision =
                evaluateMerge(pullRequestNumber);

            if (!decision.eligible()) {
                throw new IllegalStateException(
                    String.join(
                        System.lineSeparator(),
                        decision.reasons()
                    )
                );
            }

            pullRequest.merge();

            recordEvent(
                ProjectEventType.MERGED,
                "Pull Request #" +
                    pullRequestNumber +
                    " merged into " +
                    pullRequest.targetBranch(),
                actor,
                pullRequest.milestoneId(),
                ""
            );
        }

        void synchronize(
            int pullRequestNumber,
            String commit,
            String actor
        ) {
            PullRequest pullRequest =
                pullRequest(pullRequestNumber);

            BranchProtectionPolicy policy =
                branchPolicies.get(
                    pullRequest.targetBranch()
                );

            pullRequest.synchronize(
                commit,
                policy != null &&
                policy.dismissStaleApprovals()
            );

            recordEvent(
                ProjectEventType.PULL_REQUEST_OPENED,
                "Pull Request #" +
                    pullRequestNumber +
                    " synchronized",
                actor,
                pullRequest.milestoneId(),
                "New commit=" + commit
            );
        }

        List<ProjectEvent> importantEvents(
            String milestoneId
        ) {
            EnumSet<ProjectEventType> important =
                EnumSet.of(
                    ProjectEventType.PROJECT_STARTED,
                    ProjectEventType.REQUIREMENT_APPROVED,
                    ProjectEventType.DESIGN_COMPLETED,
                    ProjectEventType.PULL_REQUEST_OPENED,
                    ProjectEventType.APPROVAL_GRANTED,
                    ProjectEventType.STATUS_CHECK_FAILED,
                    ProjectEventType.STATUS_CHECK_PASSED,
                    ProjectEventType.MERGED,
                    ProjectEventType.RELEASED,
                    ProjectEventType.MILESTONE_COMPLETED,
                    ProjectEventType.MILESTONE_BLOCKED
                );

            return events.stream()
                .filter(event -> important.contains(event.type()))
                .filter(
                    event ->
                        milestoneId == null ||
                        milestoneId.equals(event.milestoneId())
                )
                .toList();
        }

        List<ProjectEvent> events() {
            return List.copyOf(events);
        }

        private Milestone milestone(String id) {
            Milestone milestone = milestones.get(id);

            if (milestone == null) {
                throw new IllegalArgumentException(
                    "Unknown milestone: " + id
                );
            }

            return milestone;
        }

        private PullRequest pullRequest(int number) {
            PullRequest pullRequest =
                pullRequests.get(number);

            if (pullRequest == null) {
                throw new IllegalArgumentException(
                    "Unknown Pull Request #" + number
                );
            }

            return pullRequest;
        }
    }

    public static void main(String[] args) {
        RepositoryGovernanceService service =
            new RepositoryGovernanceService();

        service.addMilestone(
            new Milestone(
                "M1",
                "Requirements Baseline",
                "Approved requirements for the enterprise billing service.",
                LocalDate.now().plusDays(7),
                5,
                Set.of()
            )
        );

        service.addMilestone(
            new Milestone(
                "M2",
                "Billing Service Implementation",
                "Reviewed and tested billing implementation.",
                LocalDate.now().plusDays(30),
                5,
                Set.of("M1")
            )
        );

        service.addMilestone(
            new Milestone(
                "M3",
                "Production Release",
                "Production release after repository governance checks.",
                LocalDate.now().plusDays(45),
                5,
                Set.of("M2")
            )
        );

        service.recordEvent(
            ProjectEventType.PROJECT_STARTED,
            "Billing modernization started",
            "program-manager",
            "M1",
            ""
        );

        service.activateMilestone("M1");

        service.recordEvent(
            ProjectEventType.REQUIREMENT_APPROVED,
            "Billing requirements approved",
            "product-owner",
            "M1",
            "Scope baseline accepted."
        );

        service.completeMilestone(
            "M1",
            "product-owner",
            "Requirements formally accepted."
        );

        service.activateMilestone("M2");

        service.recordEvent(
            ProjectEventType.DESIGN_COMPLETED,
            "Billing service architecture completed",
            "architect",
            "M2",
            "Architecture review passed."
        );

        service.configureBranchProtection(
            new BranchProtectionPolicy(
                "main",
                2,
                Set.of(
                    "unit-tests",
                    "integration-tests",
                    "security-scan"
                ),
                true,
                true,
                false,
                false,
                true,
                true
            )
        );

        PullRequest pullRequest =
            new PullRequest(
                914,
                "feature/billing-service",
                "main",
                "M2",
                List.of(
                    "Implement billing calculation",
                    "Add reconciliation rules",
                    "Add security validation"
                ),
                true
            );

        service.openPullRequest(
            pullRequest,
            "developer"
        );

        pullRequest.markReady();

        service.submitReview(
            914,
            new Review(
                "senior-engineer",
                ReviewState.APPROVED,
                2,
                2
            )
        );

        service.submitReview(
            914,
            new Review(
                "security-reviewer",
                ReviewState.COMMENTED,
                1,
                0
            )
        );

        System.out.println(
            "Initial merge decision: " +
            service.evaluateMerge(914)
        );

        service.submitReview(
            914,
            new Review(
                "security-reviewer",
                ReviewState.APPROVED,
                1,
                1
            )
        );

        service.updateStatusCheck(
            914,
            "unit-tests",
            true,
            "ci"
        );

        service.updateStatusCheck(
            914,
            "integration-tests",
            true,
            "ci"
        );

        service.updateStatusCheck(
            914,
            "security-scan",
            true,
            "security-ci"
        );

        System.out.println(
            "Final merge decision: " +
            service.evaluateMerge(914)
        );

        service.merge(
            914,
            "release-manager"
        );

        service.completeMilestone(
            "M2",
            "engineering-manager",
            "Implementation merged after required review and protected-branch checks."
        );

        service.activateMilestone("M3");

        service.recordEvent(
            ProjectEventType.RELEASED,
            "Billing service 4.0 released to production",
            "release-manager",
            "M3",
            "Production validation passed."
        );

        service.completeMilestone(
            "M3",
            "release-manager",
            "Release milestone completed."
        );

        System.out.println("\nIMPORTANT EVENTS");

        for (
            ProjectEvent event :
            service.importantEvents(null)
        ) {
            System.out.printf(
                "%s | %s | %s | milestone=%s%n",
                event.occurredAt(),
                event.type(),
                event.title(),
                event.milestoneId()
            );
        }
    }
}
