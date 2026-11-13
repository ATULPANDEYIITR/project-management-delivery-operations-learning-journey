import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/*
 * Java 17 Enterprise Project Status Reporting System.
 *
 * Enterprise capabilities:
 * - Immutable domain records
 * - Project delivery monitoring
 * - Schedule and financial reporting
 * - Risk assessment
 * - Pull Request lifecycle
 * - Review and approval policies
 * - Branch protection
 * - Merge eligibility service
 * - Report generation and validation
 */

public class Main {

    enum ProjectHealth {
        NOT_STARTED, ON_TRACK, AT_RISK, DELAYED, COMPLETED
    }

    enum TaskState {
        TODO, IN_PROGRESS, BLOCKED, COMPLETED
    }

    enum Priority {
        LOW, MEDIUM, HIGH, CRITICAL
    }

    enum RiskState {
        OPEN, MITIGATING, CLOSED
    }

    enum PullRequestState {
        DRAFT, OPEN, MERGED, CLOSED
    }

    enum ReviewState {
        PENDING, APPROVED, CHANGES_REQUESTED, COMMENTED, DISMISSED
    }

    enum MergeStrategy {
        MERGE_COMMIT, SQUASH, REBASE
    }

    static class DomainException extends RuntimeException {
        DomainException(String message) {
            super(message);
        }
    }

    static void requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new DomainException(field + " is required.");
        }
    }

    record Task(
        String id,
        String title,
        String owner,
        TaskState state,
        Priority priority,
        double estimatedHours,
        double actualHours
    ) {
        Task {
            requireText(id, "Task ID");
            requireText(title, "Task title");
            requireText(owner, "Task owner");
            Objects.requireNonNull(state);
            Objects.requireNonNull(priority);

            if (
                !Double.isFinite(estimatedHours) ||
                !Double.isFinite(actualHours) ||
                estimatedHours <= 0 ||
                actualHours < 0
            ) {
                throw new DomainException("Invalid task hours.");
            }
        }
    }

    record Milestone(
        String id,
        String name,
        LocalDate dueDate,
        boolean completed
    ) {
        Milestone {
            requireText(id, "Milestone ID");
            requireText(name, "Milestone name");
            Objects.requireNonNull(dueDate);
        }
    }

    record Risk(
        String id,
        String description,
        String owner,
        String mitigation,
        int probability,
        int impact,
        RiskState state
    ) {
        Risk {
            requireText(id, "Risk ID");
            requireText(description, "Risk description");
            requireText(owner, "Risk owner");
            requireText(mitigation, "Risk mitigation");

            if (
                probability < 1 || probability > 5 ||
                impact < 1 || impact > 5
            ) {
                throw new DomainException(
                    "Risk probability and impact must be between 1 and 5."
                );
            }

            Objects.requireNonNull(state);
        }

        int exposure() {
            return probability * impact;
        }

        boolean active() {
            return state != RiskState.CLOSED;
        }
    }

    record Review(
        String reviewer,
        ReviewState state,
        boolean eligible,
        boolean dismissed
    ) {
        Review {
            requireText(reviewer, "Reviewer");
            Objects.requireNonNull(state);
        }
    }

    record StatusCheck(
        String name,
        boolean passed
    ) {
        StatusCheck {
            requireText(name, "Status check");
        }
    }

    record PullRequest(
        String id,
        String title,
        String sourceBranch,
        String targetBranch,
        PullRequestState state,
        MergeStrategy strategy,
        int commits,
        boolean draft,
        boolean conflicts,
        boolean synchronizedWithBase,
        boolean conversationsResolved,
        List<Review> reviews,
        List<StatusCheck> checks
    ) {
        PullRequest {
            requireText(id, "Pull Request ID");
            requireText(title, "Pull Request title");
            requireText(sourceBranch, "Source branch");
            requireText(targetBranch, "Target branch");

            if (sourceBranch.equals(targetBranch)) {
                throw new DomainException(
                    "Source and target branches must differ."
                );
            }

            if (commits < 0) {
                throw new DomainException("Invalid commit count.");
            }

            Objects.requireNonNull(state);
            Objects.requireNonNull(strategy);

            reviews = List.copyOf(reviews);
            checks = List.copyOf(checks);
        }

        long approvalCount() {
            return reviews.stream()
                .filter(review ->
                    review.eligible() &&
                    !review.dismissed() &&
                    review.state() == ReviewState.APPROVED
                )
                .map(Review::reviewer)
                .distinct()
                .count();
        }
    }

    record BranchProtectionPolicy(
        String branch,
        int requiredApprovals,
        Set<String> requiredChecks,
        boolean requireConversations,
        boolean requireSynchronization,
        boolean requireLinearHistory,
        boolean allowDirectPush,
        boolean allowForcePush,
        boolean allowDeletion,
        boolean allowAdministratorBypass
    ) {
        BranchProtectionPolicy {
            requireText(branch, "Protected branch");

            if (requiredApprovals < 0) {
                throw new DomainException(
                    "Required approvals cannot be negative."
                );
            }

            requiredChecks = Set.copyOf(requiredChecks);
        }
    }

    record Project(
        String id,
        String name,
        String manager,
        LocalDate startDate,
        LocalDate targetDate,
        double budget,
        double actualCost,
        List<Task> tasks,
        List<Milestone> milestones,
        List<Risk> risks,
        List<PullRequest> pullRequests
    ) {
        Project {
            requireText(id, "Project ID");
            requireText(name, "Project name");
            requireText(manager, "Project manager");

            Objects.requireNonNull(startDate);
            Objects.requireNonNull(targetDate);

            if (targetDate.isBefore(startDate)) {
                throw new DomainException("Invalid project dates.");
            }

            if (
                !Double.isFinite(budget) ||
                !Double.isFinite(actualCost) ||
                budget <= 0 ||
                actualCost < 0
            ) {
                throw new DomainException("Invalid project financials.");
            }

            tasks = List.copyOf(tasks);
            milestones = List.copyOf(milestones);
            risks = List.copyOf(risks);
            pullRequests = List.copyOf(pullRequests);

            ensureUnique(tasks.stream().map(Task::id).toList(), "task");
            ensureUnique(
                milestones.stream().map(Milestone::id).toList(),
                "milestone"
            );
            ensureUnique(risks.stream().map(Risk::id).toList(), "risk");
            ensureUnique(
                pullRequests.stream().map(PullRequest::id).toList(),
                "Pull Request"
            );
        }
    }

    static void ensureUnique(List<String> identifiers, String type) {
        if (new HashSet<>(identifiers).size() != identifiers.size()) {
            throw new DomainException("Duplicate " + type + " identifier.");
        }
    }

    record GovernanceResult(
        String pullRequestId,
        boolean eligible,
        List<String> reasons
    ) {
        GovernanceResult {
            reasons = List.copyOf(reasons);
        }
    }

    interface MergePolicyEvaluator {
        GovernanceResult evaluate(
            PullRequest pullRequest,
            BranchProtectionPolicy policy
        );
    }

    static class MergeEligibilityService
        implements MergePolicyEvaluator {

        @Override
        public GovernanceResult evaluate(
            PullRequest pr,
            BranchProtectionPolicy policy
        ) {
            List<String> reasons = new ArrayList<>();

            if (pr.state() != PullRequestState.OPEN) {
                reasons.add("Pull Request is not open.");
            }

            if (pr.draft()) {
                reasons.add("Draft Pull Request cannot be merged.");
            }

            if (!pr.targetBranch().equals(policy.branch())) {
                reasons.add("Protected branch mismatch.");
            }

            if (pr.commits() == 0) {
                reasons.add("No commits are available.");
            }

            if (pr.conflicts()) {
                reasons.add("Merge conflicts exist.");
            }

            if (
                policy.requireSynchronization() &&
                !pr.synchronizedWithBase()
            ) {
                reasons.add("Base branch synchronization is required.");
            }

            if (
                policy.requireConversations() &&
                !pr.conversationsResolved()
            ) {
                reasons.add("Unresolved conversations exist.");
            }

            if (pr.approvalCount() < policy.requiredApprovals()) {
                reasons.add(
                    "Insufficient approvals: " +
                    pr.approvalCount() + "/" +
                    policy.requiredApprovals()
                );
            }

            Map<String, Boolean> checks = new HashMap<>();

            pr.checks().forEach(check ->
                checks.put(check.name(), check.passed())
            );

            for (String required : policy.requiredChecks()) {
                if (!Boolean.TRUE.equals(checks.get(required))) {
                    reasons.add("Required check failed or missing: " + required);
                }
            }

            if (
                policy.requireLinearHistory() &&
                pr.strategy() == MergeStrategy.MERGE_COMMIT
            ) {
                reasons.add("Merge commit violates linear history.");
            }

            return new GovernanceResult(
                pr.id(),
                reasons.isEmpty(),
                reasons
            );
        }
    }

    static class ReportService {

        private final Project project;

        ReportService(Project project) {
            this.project = Objects.requireNonNull(project);
        }

        double completionPercentage() {
            if (project.tasks().isEmpty()) return 0;

            long completed = project.tasks().stream()
                .filter(task -> task.state() == TaskState.COMPLETED)
                .count();

            return round(
                completed * 100.0 / project.tasks().size()
            );
        }

        double milestoneCompletion() {
            if (project.milestones().isEmpty()) return 0;

            long completed = project.milestones().stream()
                .filter(Milestone::completed)
                .count();

            return round(
                completed * 100.0 / project.milestones().size()
            );
        }

        double budgetVariance() {
            return project.actualCost() - project.budget();
        }

        double budgetUtilization() {
            return round(
                project.actualCost() / project.budget() * 100
            );
        }

        long remainingDays() {
            return java.time.temporal.ChronoUnit.DAYS.between(
                LocalDate.now(),
                project.targetDate()
            );
        }

        ProjectHealth calculateHealth() {

            if (
                !project.tasks().isEmpty() &&
                completionPercentage() == 100
            ) {
                return ProjectHealth.COMPLETED;
            }

            if (budgetUtilization() > 100 || remainingDays() < 0) {
                return ProjectHealth.DELAYED;
            }

            boolean criticalBlock = project.tasks().stream()
                .anyMatch(task ->
                    task.state() == TaskState.BLOCKED &&
                    (
                        task.priority() == Priority.HIGH ||
                        task.priority() == Priority.CRITICAL
                    )
                );

            boolean criticalRisk = project.risks().stream()
                .anyMatch(risk -> risk.active() && risk.exposure() >= 15);

            if (criticalBlock || criticalRisk) {
                return ProjectHealth.AT_RISK;
            }

            return project.tasks().isEmpty()
                ? ProjectHealth.NOT_STARTED
                : ProjectHealth.ON_TRACK;
        }

        Map<String, Object> deliveryMetrics() {

            Map<String, Object> result = new HashMap<>();

            result.put("total", project.tasks().size());

            for (TaskState state : TaskState.values()) {
                long count = project.tasks().stream()
                    .filter(task -> task.state() == state)
                    .count();

                result.put(state.name().toLowerCase(), count);
            }

            result.put(
                "estimatedHours",
                project.tasks().stream()
                    .mapToDouble(Task::estimatedHours)
                    .sum()
            );

            result.put(
                "actualHours",
                project.tasks().stream()
                    .mapToDouble(Task::actualHours)
                    .sum()
            );

            return result;
        }

        List<Map<String, Object>> activeRisks() {

            return project.risks().stream()
                .filter(Risk::active)
                .sorted(
                    Comparator.comparingInt(Risk::exposure).reversed()
                )
                .map(risk -> {
                    Map<String, Object> item = new HashMap<>();

                    item.put("id", risk.id());
                    item.put("description", risk.description());
                    item.put("owner", risk.owner());
                    item.put("exposure", risk.exposure());
                    item.put("mitigation", risk.mitigation());

                    return item;
                })
                .toList();
        }

        Map<String, Object> repositoryMetrics() {

            Map<String, Object> metrics = new HashMap<>();

            metrics.put("total", project.pullRequests().size());

            for (PullRequestState state : PullRequestState.values()) {
                metrics.put(
                    state.name().toLowerCase(),
                    project.pullRequests().stream()
                        .filter(pr -> pr.state() == state)
                        .count()
                );
            }

            metrics.put(
                "approvals",
                project.pullRequests().stream()
                    .mapToLong(PullRequest::approvalCount)
                    .sum()
            );

            return metrics;
        }

        Map<String, Object> generate() {

            Map<String, Object> report = new HashMap<>();

            Map<String, Object> metadata = new HashMap<>();

            metadata.put("reportId", UUID.randomUUID().toString());
            metadata.put("generatedAt", OffsetDateTime.now().toString());
            metadata.put("projectId", project.id());
            metadata.put("projectName", project.name());
            metadata.put("manager", project.manager());

            report.put("metadata", metadata);
            report.put("health", calculateHealth().name());
            report.put("completionPercentage", completionPercentage());
            report.put("milestoneCompletion", milestoneCompletion());

            Map<String, Object> schedule = new HashMap<>();

            schedule.put("startDate", project.startDate());
            schedule.put("targetDate", project.targetDate());
            schedule.put("remainingDays", remainingDays());

            report.put("schedule", schedule);

            Map<String, Object> financials = new HashMap<>();

            financials.put("budget", project.budget());
            financials.put("actualCost", project.actualCost());
            financials.put("variance", budgetVariance());
            financials.put("utilization", budgetUtilization());

            report.put("financials", financials);
            report.put("delivery", deliveryMetrics());
            report.put("activeRisks", activeRisks());
            report.put("repository", repositoryMetrics());

            return report;
        }

        private double round(double value) {
            return Math.round(value * 100.0) / 100.0;
        }
    }

    static Project createDemoProject() {

        List<Task> tasks = List.of(
            new Task(
                "T001", "Requirements analysis", "Analyst",
                TaskState.COMPLETED, Priority.HIGH, 80, 76
            ),
            new Task(
                "T002", "Database implementation", "Developer",
                TaskState.COMPLETED, Priority.HIGH, 120, 130
            ),
            new Task(
                "T003", "Reporting engine", "Developer",
                TaskState.IN_PROGRESS, Priority.HIGH, 160, 70
            ),
            new Task(
                "T004", "Security testing", "Security Lead",
                TaskState.BLOCKED, Priority.CRITICAL, 60, 15
            ),
            new Task(
                "T005", "Deployment preparation", "Operations",
                TaskState.TODO, Priority.MEDIUM, 50, 0
            )
        );

        List<Milestone> milestones = List.of(
            new Milestone(
                "M001", "Requirements approved",
                LocalDate.of(2026, 10, 1), true
            ),
            new Milestone(
                "M002", "Database completed",
                LocalDate.of(2026, 11, 20), true
            ),
            new Milestone(
                "M003", "System testing",
                LocalDate.of(2027, 1, 15), false
            )
        );

        List<Risk> risks = List.of(
            new Risk(
                "R001",
                "Security testing environment unavailable",
                "Security Lead",
                "Provision isolated testing infrastructure",
                4, 5, RiskState.OPEN
            ),
            new Risk(
                "R002",
                "Reporting data quality issues",
                "Data Lead",
                "Introduce automated validation",
                3, 3, RiskState.MITIGATING
            ),
            new Risk(
                "R003",
                "Requirements clarification completed",
                "Analyst",
                "Maintain approved requirements",
                1, 2, RiskState.CLOSED
            )
        );

        List<Review> approvedReviews = List.of(
            new Review(
                "reviewer-a", ReviewState.APPROVED, true, false
            ),
            new Review(
                "reviewer-b", ReviewState.APPROVED, true, false
            )
        );

        List<StatusCheck> successfulChecks = List.of(
            new StatusCheck("unit-tests", true),
            new StatusCheck("security-scan", true),
            new StatusCheck("lint", true)
        );

        PullRequest validPR = new PullRequest(
            "PR-101",
            "Implement reporting API",
            "feature/reporting",
            "main",
            PullRequestState.OPEN,
            MergeStrategy.SQUASH,
            4,
            false,
            false,
            true,
            true,
            approvedReviews,
            successfulChecks
        );

        PullRequest blockedPR = new PullRequest(
            "PR-102",
            "Implement security controls",
            "feature/security",
            "main",
            PullRequestState.OPEN,
            MergeStrategy.SQUASH,
            2,
            true,
            false,
            true,
            false,
            List.of(
                new Review(
                    "reviewer-c",
                    ReviewState.CHANGES_REQUESTED,
                    true,
                    false
                )
            ),
            List.of(
                new StatusCheck("unit-tests", true),
                new StatusCheck("security-scan", false)
            )
        );

        return new Project(
            "PRJ-2026-001",
            "Enterprise Project Reporting Platform",
            "Project Manager",
            LocalDate.of(2026, 9, 1),
            LocalDate.of(2027, 2, 28),
            500000,
            185000,
            tasks,
            milestones,
            risks,
            List.of(validPR, blockedPR)
        );
    }

    static void runTests() {

        Project project = createDemoProject();

        ReportService service = new ReportService(project);

        if (service.completionPercentage() != 40.0) {
            throw new DomainException("Completion test failed.");
        }

        if (service.calculateHealth() != ProjectHealth.AT_RISK) {
            throw new DomainException("Health classification test failed.");
        }

        BranchProtectionPolicy policy = new BranchProtectionPolicy(
            "main",
            2,
            Set.of("unit-tests", "security-scan", "lint"),
            true,
            true,
            true,
            false,
            false,
            false,
            false
        );

        MergeEligibilityService engine = new MergeEligibilityService();

        GovernanceResult valid = engine.evaluate(
            project.pullRequests().get(0), policy
        );

        if (!valid.eligible()) {
            throw new DomainException("Valid PR rejected.");
        }

        GovernanceResult blocked = engine.evaluate(
            project.pullRequests().get(1), policy
        );

        if (blocked.eligible()) {
            throw new DomainException("Invalid PR accepted.");
        }

        System.out.println("All enterprise validation tests passed.");
    }

    public static void main(String[] args) {

        try {

            runTests();

            Project project = createDemoProject();

            ReportService reporting = new ReportService(project);

            Map<String, Object> report = reporting.generate();

            System.out.println("\nENTERPRISE PROJECT STATUS REPORT");
            System.out.println("======================================");

            System.out.println("Project: " + project.name());
            System.out.println("Manager: " + project.manager());
            System.out.println("Health: " + report.get("health"));

            System.out.println(
                "Completion: " +
                report.get("completionPercentage") + "%"
            );

            System.out.println(
                "Milestone completion: " +
                report.get("milestoneCompletion") + "%"
            );

            System.out.println("Delivery: " + report.get("delivery"));
            System.out.println("Financials: " + report.get("financials"));
            System.out.println("Active risks: " + report.get("activeRisks"));

            BranchProtectionPolicy policy = new BranchProtectionPolicy(
                "main",
                2,
                Set.of("unit-tests", "security-scan", "lint"),
                true,
                true,
                true,
                false,
                false,
                false,
                false
            );

            MergeEligibilityService engine = new MergeEligibilityService();

            System.out.println("\nMERGE ELIGIBILITY");

            for (PullRequest pr : project.pullRequests()) {

                GovernanceResult result = engine.evaluate(pr, policy);

                System.out.println(
                    "\n" + result.pullRequestId() + ": " +
                    (result.eligible() ? "ELIGIBLE" : "BLOCKED")
                );

                result.reasons().forEach(
                    reason -> System.out.println(" - " + reason)
                );
            }

            System.out.println("\nReport generation completed.");

        } catch (DomainException exception) {

            System.err.println(
                "Domain validation failed: " + exception.getMessage()
            );

            System.exit(1);

        } catch (Exception exception) {

            System.err.println(
                "Unexpected failure: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
