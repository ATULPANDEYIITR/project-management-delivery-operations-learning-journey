import java.util.*;
import java.util.stream.Collectors;

public class RepositoryGovernance {

    enum PRState {
        DRAFT, OPEN, CLOSED, MERGED
    }

    enum ReviewState {
        COMMENTED, APPROVED, CHANGES_REQUESTED, DISMISSED
    }

    enum CheckState {
        PASSING, FAILING, PENDING
    }

    static class GovernanceException extends RuntimeException {
        GovernanceException(String message) {
            super(message);
        }
    }

    record Person(String username, String role, Set<String> teams) {
        Person {
            teams = Set.copyOf(teams);
        }

        boolean canReview() {
            return teams.contains("reviewer") || teams.contains("maintainer");
        }
    }

    record Commit(String sha, String message, String author) {
        Commit {
            if (!sha.matches("[a-zA-Z0-9]{7,40}")) {
                throw new GovernanceException("Invalid commit SHA.");
            }
        }
    }

    record Review(
        String reviewer,
        ReviewState state,
        String commitSha
    ) {}

    record StatusCheck(String name, CheckState state) {}

    record BranchProtection(
        int requiredReviews,
        Set<String> requiredChecks,
        boolean requireConversationResolution,
        boolean requireLinearHistory,
        boolean allowForcePush,
        boolean allowDeletion,
        boolean allowDirectPush
    ) {
        BranchProtection {
            if (requiredReviews < 0) {
                throw new GovernanceException(
                    "Required review count cannot be negative."
                );
            }
            requiredChecks = Set.copyOf(requiredChecks);
        }
    }

    static final class PullRequest {
        private final int number;
        private final String title;
        private final String author;
        private final String source;
        private final String target;

        private PRState state = PRState.OPEN;
        private boolean draft;
        private boolean mergeable = true;
        private int baseBehindBy;
        private int unresolvedConversations;

        private final List<Commit> commits = new ArrayList<>();
        private final List<Review> reviews = new ArrayList<>();
        private final Map<String, StatusCheck> checks = new HashMap<>();

        PullRequest(
            int number,
            String title,
            String author,
            String source,
            String target
        ) {
            this.number = number;
            this.title = Objects.requireNonNull(title);
            this.author = Objects.requireNonNull(author);
            this.source = Objects.requireNonNull(source);
            this.target = Objects.requireNonNull(target);
        }

        void addCommit(Commit commit) {
            if (state != PRState.OPEN && state != PRState.DRAFT) {
                throw new GovernanceException(
                    "Commits cannot be added in the current state."
                );
            }
            commits.add(commit);
        }

        void addReview(Review review) {
            if (review.reviewer().equals(author)) {
                throw new GovernanceException(
                    "Authors cannot approve their own pull request."
                );
            }

            boolean referencesKnownCommit = commits.stream()
                .anyMatch(c -> c.sha().equals(review.commitSha()));

            if (!referencesKnownCommit) {
                throw new GovernanceException(
                    "Review references an unknown commit."
                );
            }

            reviews.add(review);
        }

        void setCheck(String name, CheckState state) {
            checks.put(name, new StatusCheck(name, state));
        }

        void setUnresolvedConversations(int count) {
            if (count < 0) {
                throw new GovernanceException(
                    "Conversation count cannot be negative."
                );
            }
            unresolvedConversations = count;
        }

        void setBaseBehindBy(int count) {
            if (count < 0) {
                throw new GovernanceException(
                    "Base divergence cannot be negative."
                );
            }
            baseBehindBy = count;
        }

        int number() {
            return number;
        }

        String title() {
            return title;
        }

        String author() {
            return author;
        }

        String target() {
            return target;
        }

        PRState state() {
            return state;
        }

        boolean draft() {
            return draft;
        }

        boolean mergeable() {
            return mergeable;
        }

        int baseBehindBy() {
            return baseBehindBy;
        }

        int unresolvedConversations() {
            return unresolvedConversations;
        }

        List<Commit> commits() {
            return List.copyOf(commits);
        }

        List<Review> reviews() {
            return List.copyOf(reviews);
        }

        Map<String, StatusCheck> checks() {
            return Map.copyOf(checks);
        }
    }

    interface EligibilityRule {
        Optional<String> validate(
            PullRequest pr,
            BranchProtection policy,
            Map<String, Person> members
        );
    }

    static class ReviewRequirement implements EligibilityRule {
        @Override
        public Optional<String> validate(
            PullRequest pr,
            BranchProtection policy,
            Map<String, Person> members
        ) {
            if (pr.commits().isEmpty()) {
                return Optional.of("No commits are present.");
            }

            String head = pr.commits().getLast().sha();

            Set<String> approvers = pr.reviews().stream()
                .filter(r -> r.state() == ReviewState.APPROVED)
                .filter(r -> r.commitSha().equals(head))
                .filter(r -> !r.reviewer().equals(pr.author()))
                .filter(r -> members.containsKey(r.reviewer()))
                .filter(r -> members.get(r.reviewer()).canReview())
                .map(Review::reviewer)
                .collect(Collectors.toSet());

            if (approvers.size() < policy.requiredReviews()) {
                return Optional.of(
                    "Required current approval count has not been reached."
                );
            }

            return Optional.empty();
        }
    }

    static class StatusCheckRule implements EligibilityRule {
        @Override
        public Optional<String> validate(
            PullRequest pr,
            BranchProtection policy,
            Map<String, Person> members
        ) {
            for (String required : policy.requiredChecks()) {
                StatusCheck check = pr.checks().get(required);
                if (check == null || check.state() != CheckState.PASSING) {
                    return Optional.of(
                        "Required check '" + required + "' is not passing."
                    );
                }
            }
            return Optional.empty();
        }
    }

    static class RepositoryService {
        private final Map<String, Person> members;
        private final Map<String, BranchProtection> policies;
        private final List<EligibilityRule> rules = List.of(
            new ReviewRequirement(),
            new StatusCheckRule()
        );

        RepositoryService(
            Collection<Person> members,
            Map<String, BranchProtection> policies
        ) {
            this.members = members.stream()
                .collect(Collectors.toUnmodifiableMap(
                    Person::username,
                    p -> p
                ));
            this.policies = Map.copyOf(policies);
        }

        List<String> evaluate(PullRequest pr) {
            List<String> failures = new ArrayList<>();
            BranchProtection policy = policies.get(pr.target());

            if (pr.state() != PRState.OPEN) {
                failures.add("Pull request is not open.");
            }

            if (pr.draft()) {
                failures.add("Draft pull request cannot be merged.");
            }

            if (!pr.mergeable()) {
                failures.add("Merge conflicts are present.");
            }

            if (policy == null) {
                failures.add("Target branch is not protected.");
                return failures;
            }

            for (EligibilityRule rule : rules) {
                rule.validate(pr, policy, members)
                    .ifPresent(failures::add);
            }

            if (
                policy.requireConversationResolution() &&
                pr.unresolvedConversations() > 0
            ) {
                failures.add("Unresolved review conversations remain.");
            }

            if (
                policy.requireLinearHistory() &&
                pr.baseBehindBy() > 0
            ) {
                failures.add(
                    "Source branch must synchronize with the base branch."
                );
            }

            return failures;
        }
    }

    private static void printDecision(
        RepositoryService service,
        PullRequest pr
    ) {
        List<String> failures = service.evaluate(pr);

        System.out.println(
            "PR #" + pr.number() + ": " + pr.title() + " -> " +
            (failures.isEmpty()
                ? "MERGE ELIGIBLE"
                : "MERGE BLOCKED")
        );

        failures.forEach(f -> System.out.println("  - " + f));
    }

    public static void main(String[] args) {
        List<Person> members = List.of(
            new Person("atul", "developer", Set.of("developer")),
            new Person("maya", "reviewer", Set.of("reviewer")),
            new Person("liam", "maintainer", Set.of("maintainer")),
            new Person("nora", "reviewer", Set.of("reviewer"))
        );

        BranchProtection mainPolicy = new BranchProtection(
            2,
            Set.of("ci", "security"),
            true,
            true,
            false,
            false,
            false
        );

        RepositoryService service = new RepositoryService(
            members,
            Map.of("main", mainPolicy)
        );

        PullRequest pr = new PullRequest(
            142,
            "Add transaction idempotency protection",
            "atul",
            "feature/idempotency",
            "main"
        );

        Commit first = new Commit(
            "a1b2c3d",
            "Add idempotency validation",
            "atul"
        );

        pr.addCommit(first);
        pr.setCheck("ci", CheckState.PASSING);
        pr.setCheck("security", CheckState.PASSING);

        pr.addReview(new Review(
            "maya",
            ReviewState.APPROVED,
            first.sha()
        ));

        pr.addReview(new Review(
            "liam",
            ReviewState.APPROVED,
            first.sha()
        ));

        printDecision(service, pr);
        System.out.println();

        Commit second = new Commit(
            "d4e5f6g",
            "Handle duplicate transaction requests",
            "atul"
        );

        pr.addCommit(second);
        printDecision(service, pr);
        System.out.println();

        pr.addReview(new Review(
            "maya",
            ReviewState.APPROVED,
            second.sha()
        ));

        pr.addReview(new Review(
            "liam",
            ReviewState.APPROVED,
            second.sha()
        ));

        pr.setUnresolvedConversations(1);
        printDecision(service, pr);
        System.out.println();

        pr.setUnresolvedConversations(0);
        printDecision(service, pr);

        try {
            pr.addReview(new Review(
                "atul",
                ReviewState.APPROVED,
                second.sha()
            ));
        } catch (GovernanceException ex) {
            System.out.println("Validation failure: " + ex.getMessage());
        }
    }
}
