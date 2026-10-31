import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class ResourceGovernanceApp {

    enum PRState {
        DRAFT, OPEN, CLOSED, MERGED
    }

    enum ReviewState {
        COMMENTED, APPROVED, CHANGES_REQUESTED, DISMISSED
    }

    enum ResourceType {
        ENGINEER, REVIEWER, AUTOMATION
    }

    record Resource(
            String id,
            ResourceType type,
            double capacityHours,
            double hourlyCost) {

        Resource {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("Resource id is required");
            }
            if (capacityHours <= 0 || hourlyCost < 0) {
                throw new IllegalArgumentException("Invalid resource capacity or cost");
            }
        }
    }

    record Commit(String sha, String message, String author, Instant createdAt) {
        Commit {
            if (sha == null || sha.length() < 7) {
                throw new IllegalArgumentException("Invalid commit SHA");
            }
            if (message == null || message.isBlank()) {
                throw new IllegalArgumentException("Commit message is required");
            }
        }
    }

    record ReviewComment(
            String reviewer,
            String file,
            int line,
            String message,
            boolean resolved) {
    }

    record Review(
            String reviewer,
            ReviewState state,
            String commitSha,
            List<ReviewComment> comments) {

        Review {
            comments = List.copyOf(comments);
        }
    }

    record StatusCheck(String name, boolean passed) {
    }

    static final class BranchProtection {
        private final int requiredApprovals;
        private final Set<String> requiredChecks;
        private final boolean requireResolvedConversations;
        private final boolean requireLinearHistory;
        private final boolean allowDirectPush;
        private final boolean allowForcePush;

        BranchProtection(
                int requiredApprovals,
                Set<String> requiredChecks,
                boolean requireResolvedConversations,
                boolean requireLinearHistory,
                boolean allowDirectPush,
                boolean allowForcePush) {

            if (requiredApprovals < 0) {
                throw new IllegalArgumentException("Approval requirement cannot be negative");
            }

            this.requiredApprovals = requiredApprovals;
            this.requiredChecks = Set.copyOf(requiredChecks);
            this.requireResolvedConversations = requireResolvedConversations;
            this.requireLinearHistory = requireLinearHistory;
            this.allowDirectPush = allowDirectPush;
            this.allowForcePush = allowForcePush;
        }
    }

    static final class ResourceAllocationService {
        private final Map<String, Resource> resources;
        private final Map<String, Double> allocations = new HashMap<>();

        ResourceAllocationService(List<Resource> resources) {
            this.resources = new HashMap<>();

            for (Resource resource : resources) {
                if (this.resources.putIfAbsent(resource.id(), resource) != null) {
                    throw new IllegalArgumentException(
                            "Duplicate resource: " + resource.id());
                }
                allocations.put(resource.id(), 0.0);
            }
        }

        void allocate(String resourceId, double hours) {
            Resource resource = resources.get(resourceId);
            if (resource == null) {
                throw new IllegalArgumentException("Unknown resource");
            }
            if (!Double.isFinite(hours) || hours <= 0) {
                throw new IllegalArgumentException("Hours must be positive and finite");
            }

            double current = allocations.get(resourceId);
            if (current + hours > resource.capacityHours()) {
                throw new ResourceCapacityException(
                        resourceId,
                        current + hours,
                        resource.capacityHours());
            }

            allocations.put(resourceId, current + hours);
        }

        double totalCost() {
            return resources.entrySet()
                    .stream()
                    .mapToDouble(entry ->
                            allocations.get(entry.getKey())
                                    * entry.getValue().hourlyCost())
                    .sum();
        }

        List<String> utilizationReport() {
            return resources.values()
                    .stream()
                    .sorted((a, b) -> a.id().compareTo(b.id()))
                    .map(resource -> {
                        double used = allocations.get(resource.id());
                        double ratio = used / resource.capacityHours();
                        return "%s: %.1fh / %.1fh (%.1f%%)"
                                .formatted(
                                        resource.id(),
                                        used,
                                        resource.capacityHours(),
                                        ratio * 100);
                    })
                    .toList();
        }
    }

    static final class PullRequest {
        private final int number;
        private final String sourceBranch;
        private final String targetBranch;
        private final String author;
        private final List<Commit> commits;
        private final List<Review> reviews = new ArrayList<>();
        private final List<StatusCheck> statusChecks = new ArrayList<>();

        private PRState state;
        private boolean baseSynchronized = true;

        PullRequest(
                int number,
                String sourceBranch,
                String targetBranch,
                String author,
                List<Commit> commits) {

            if (commits.isEmpty()) {
                throw new IllegalArgumentException("A PR requires commits");
            }

            this.number = number;
            this.sourceBranch = sourceBranch;
            this.targetBranch = targetBranch;
            this.author = author;
            this.commits = new ArrayList<>(commits);
            this.state = PRState.OPEN;
        }

        int number() {
            return number;
        }

        String author() {
            return author;
        }

        List<Commit> commits() {
            return List.copyOf(commits);
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        List<StatusCheck> statusChecks() {
            return List.copyOf(statusChecks);
        }

        PRState state() {
            return state;
        }

        void submitReview(Review review) {
            if (state != PRState.OPEN && state != PRState.DRAFT) {
                throw new IllegalStateException("PR is inactive");
            }
            if (review.reviewer().equals(author)) {
                throw new IllegalArgumentException("Self-review cannot approve a PR");
            }
            reviews.add(review);
        }

        void setStatusCheck(StatusCheck check) {
            statusChecks.removeIf(
                    current -> current.name().equals(check.name()));
            statusChecks.add(check);
        }

        void markBaseStale() {
            baseSynchronized = false;
        }

        void synchronizeBase() {
            baseSynchronized = true;
        }

        boolean isBaseSynchronized() {
            return baseSynchronized;
        }

        void merge() {
            state = PRState.MERGED;
        }
    }

    static final class RepositoryGovernanceService {
        private final BranchProtection protection;
        private final Map<String, List<Commit>> branches = new HashMap<>();
        private int nextPullRequest = 1;

        RepositoryGovernanceService(BranchProtection protection) {
            this.protection = protection;
            branches.put("main", new ArrayList<>());
        }

        void createBranch(String branch, String base) {
            if (branches.containsKey(branch)) {
                throw new IllegalArgumentException("Branch already exists");
            }

            List<Commit> source = branches.get(base);
            if (source == null) {
                throw new IllegalArgumentException("Unknown base branch");
            }

            branches.put(branch, new ArrayList<>(source));
        }

        void addCommit(
                String branch,
                String sha,
                String message,
                String author) {

            List<Commit> history = branches.get(branch);
            if (history == null) {
                throw new IllegalArgumentException("Unknown branch");
            }

            history.add(new Commit(
                    sha,
                    message,
                    author,
                    Instant.now()));
        }

        PullRequest openPullRequest(
                String source,
                String target,
                String author) {

            List<Commit> sourceHistory = branches.get(source);

            if (sourceHistory == null || !branches.containsKey(target)) {
                throw new IllegalArgumentException("Unknown branch");
            }
            if (source.equals(target)) {
                throw new IllegalArgumentException("Source and target must differ");
            }

            return new PullRequest(
                    nextPullRequest++,
                    source,
                    target,
                    author,
                    sourceHistory);
        }

        MergeDecision evaluate(PullRequest pr) {
            List<String> failures = new ArrayList<>();

            if (pr.state() != PRState.OPEN) {
                failures.add("PR is not open");
            }

            if (!pr.isBaseSynchronized()) {
                failures.add("Base branch is stale");
            }

            String latestCommit = pr.commits().getLast().sha();

            Set<String> approvals = pr.reviews()
                    .stream()
                    .filter(review ->
                            review.state() == ReviewState.APPROVED
                                    && review.commitSha().equals(latestCommit)
                                    && pr.isBaseSynchronized())
                    .map(Review::reviewer)
                    .collect(java.util.stream.Collectors.toSet());

            if (approvals.size() < protection.requiredApprovals) {
                failures.add("Required approvals are missing");
            }

            for (String requiredCheck : protection.requiredChecks) {
                boolean passed = pr.statusChecks()
                        .stream()
                        .anyMatch(check ->
                                check.name().equals(requiredCheck)
                                        && check.passed());

                if (!passed) {
                    failures.add("Required check failed: " + requiredCheck);
                }
            }

            if (protection.requireResolvedConversations) {
                boolean unresolved = pr.reviews()
                        .stream()
                        .flatMap(review -> review.comments().stream())
                        .anyMatch(comment -> !comment.resolved());

                if (unresolved) {
                    failures.add("Unresolved review conversations remain");
                }
            }

            if (protection.requireLinearHistory) {
                Set<String> uniqueShas = new HashSet<>(
                        pr.commits()
                                .stream()
                                .map(Commit::sha)
                                .toList());

                if (uniqueShas.size() != pr.commits().size()) {
                    failures.add("Duplicate commits violate linear-history policy");
                }
            }

            return new MergeDecision(failures.isEmpty(), failures);
        }

        void merge(PullRequest pr) {
            MergeDecision decision = evaluate(pr);

            if (!decision.eligible()) {
                throw new MergeBlockedException(decision.failures());
            }

            pr.merge();
        }
    }

    record MergeDecision(boolean eligible, List<String> failures) {
        MergeDecision {
            failures = List.copyOf(failures);
        }
    }

    static class ResourceCapacityException extends RuntimeException {
        ResourceCapacityException(
                String resource,
                double requested,
                double capacity) {
            super("Resource %s would use %.1fh against %.1fh capacity"
                    .formatted(resource, requested, capacity));
        }
    }

    static class MergeBlockedException extends RuntimeException {
        MergeBlockedException(List<String> failures) {
            super("Merge blocked: " + String.join("; ", failures));
        }
    }

    public static void main(String[] args) {
        ResourceAllocationService resources =
                new ResourceAllocationService(List.of(
                        new Resource(
                                "engineer-01",
                                ResourceType.ENGINEER,
                                32,
                                85),
                        new Resource(
                                "reviewer-01",
                                ResourceType.REVIEWER,
                                16,
                                110),
                        new Resource(
                                "ci-01",
                                ResourceType.AUTOMATION,
                                20,
                                20)
                ));

        resources.allocate("engineer-01", 13);
        resources.allocate("reviewer-01", 4);
        resources.allocate("ci-01", 2);

        BranchProtection protection = new BranchProtection(
                1,
                Set.of("unit-tests", "security-scan"),
                true,
                true,
                false,
                false);

        RepositoryGovernanceService repository =
                new RepositoryGovernanceService(protection);

        repository.createBranch("feature/resource-policy", "main");

        repository.addCommit(
                "feature/resource-policy",
                "abc1234",
                "Add resource capacity rules",
                "engineer-01");

        repository.addCommit(
                "feature/resource-policy",
                "def5678",
                "Enforce allocation limits",
                "engineer-01");

        PullRequest pr = repository.openPullRequest(
                "feature/resource-policy",
                "main",
                "engineer-01");

        pr.submitReview(new Review(
                "reviewer-01",
                ReviewState.CHANGES_REQUESTED,
                "def5678",
                List.of(new ReviewComment(
                        "reviewer-01",
                        "resource-service.java",
                        92,
                        "Reject allocations beyond capacity.",
                        false))));

        MergeDecision first = repository.evaluate(pr);
        System.out.println("Initial merge eligibility: " + first.eligible());
        System.out.println(first.failures());

        pr.submitReview(new Review(
                "reviewer-01",
                ReviewState.APPROVED,
                "def5678",
                List.of(new ReviewComment(
                        "reviewer-01",
                        "resource-service.java",
                        92,
                        "Resolved by capacity validation.",
                        true))));

        pr.setStatusCheck(new StatusCheck("unit-tests", true));
        pr.setStatusCheck(new StatusCheck("security-scan", true));

        MergeDecision second = repository.evaluate(pr);
        System.out.println("Final merge eligibility: " + second.eligible());

        if (second.eligible()) {
            repository.merge(pr);
            System.out.println("Pull request #" + pr.number() + " merged.");
        }

        System.out.println("\nResource utilization:");
        resources.utilizationReport()
                .forEach(System.out::println);

        System.out.printf(
                "Project resource cost: $%.2f%n",
                resources.totalCost());

        try {
            resources.allocate("engineer-01", 25);
        } catch (ResourceCapacityException ex) {
            System.out.println("Expected resource failure: "
                    + ex.getMessage());
        }
    }
}
