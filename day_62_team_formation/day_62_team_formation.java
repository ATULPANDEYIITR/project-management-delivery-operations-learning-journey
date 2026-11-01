import java.util.*;
import java.util.function.Predicate;
import java.util.stream.Collectors;

public class TeamFormationEnterprise {

    enum Role {
        PRODUCT_MANAGER,
        TECH_LEAD,
        BACKEND,
        FRONTEND,
        QA,
        DEVOPS,
        DATA,
        SECURITY,
        UX
    }

    enum Availability {
        AVAILABLE,
        PARTIAL,
        UNAVAILABLE
    }

    enum TeamState {
        PROPOSED,
        VALIDATED,
        APPROVED,
        REJECTED
    }

    record Candidate(
        String id,
        String name,
        Set<String> skills,
        Set<Role> roles,
        double experienceYears,
        Availability availability
    ) {
        Candidate {
            Objects.requireNonNull(id);
            Objects.requireNonNull(name);
            Objects.requireNonNull(skills);
            Objects.requireNonNull(roles);
            Objects.requireNonNull(availability);

            if (id.isBlank() || name.isBlank()) {
                throw new IllegalArgumentException("Candidate identity is required.");
            }

            if (experienceYears < 0) {
                throw new IllegalArgumentException(
                    "Experience cannot be negative: " + id
                );
            }

            skills = Set.copyOf(skills);
            roles = Set.copyOf(roles);
        }
    }

    record Project(
        String id,
        String name,
        Set<String> requiredSkills,
        Set<Role> requiredRoles,
        int minimumTeamSize,
        int maximumTeamSize,
        boolean requiresSecurityReview
    ) {
        Project {
            if (minimumTeamSize < 1 ||
                maximumTeamSize < minimumTeamSize) {
                throw new IllegalArgumentException(
                    "Invalid project team-size policy."
                );
            }

            requiredSkills = Set.copyOf(requiredSkills);
            requiredRoles = Set.copyOf(requiredRoles);
        }
    }

    record TeamMember(
        Candidate candidate,
        int selectionScore
    ) {}

    record FormationDecision(
        TeamState state,
        List<String> selectedMembers,
        Set<Role> missingRoles,
        Set<String> missingSkills,
        List<String> reasons
    ) {}

    interface TeamPolicy {
        boolean accepts(Project project, List<Candidate> team);

        String rejectionReason(Project project, List<Candidate> team);
    }

    static final class MinimumCoveragePolicy implements TeamPolicy {
        @Override
        public boolean accepts(Project project, List<Candidate> team) {
            return missingRoles(project, team).isEmpty()
                && missingSkills(project, team).isEmpty()
                && team.size() >= project.minimumTeamSize()
                && team.size() <= project.maximumTeamSize();
        }

        @Override
        public String rejectionReason(Project project, List<Candidate> team) {
            List<String> reasons = new ArrayList<>();

            if (team.size() < project.minimumTeamSize()) {
                reasons.add("team is below minimum size");
            }

            if (team.size() > project.maximumTeamSize()) {
                reasons.add("team exceeds maximum size");
            }

            if (!missingRoles(project, team).isEmpty()) {
                reasons.add("mandatory roles are missing");
            }

            if (!missingSkills(project, team).isEmpty()) {
                reasons.add("mandatory skills are missing");
            }

            return String.join("; ", reasons);
        }
    }

    static final class SecurityPolicy implements TeamPolicy {
        @Override
        public boolean accepts(Project project, List<Candidate> team) {
            if (!project.requiresSecurityReview()) return true;

            return team.stream()
                .anyMatch(candidate ->
                    candidate.roles().contains(Role.SECURITY)
                );
        }

        @Override
        public String rejectionReason(Project project, List<Candidate> team) {
            return "High-risk projects require an eligible Security Engineer.";
        }
    }

    static final class TeamFormationService {
        private final List<Candidate> candidates;
        private final List<TeamPolicy> policies;

        TeamFormationService(
            List<Candidate> candidates,
            List<TeamPolicy> policies
        ) {
            this.candidates = List.copyOf(candidates);
            this.policies = List.copyOf(policies);

            Set<String> ids = new HashSet<>();

            for (Candidate candidate : this.candidates) {
                if (!ids.add(candidate.id())) {
                    throw new IllegalArgumentException(
                        "Duplicate candidate ID: " + candidate.id()
                    );
                }
            }
        }

        FormationDecision form(Project project) {
            List<Candidate> eligible = candidates.stream()
                .filter(candidate ->
                    candidate.availability() != Availability.UNAVAILABLE
                )
                .sorted(
                    Comparator.comparingDouble(
                        (Candidate candidate) ->
                            score(candidate, project)
                    ).reversed()
                )
                .toList();

            List<Candidate> team = new ArrayList<>();
            Set<String> selected = new HashSet<>();

            for (Role requiredRole : project.requiredRoles()) {
                Candidate candidate = eligible.stream()
                    .filter(person ->
                        !selected.contains(person.id())
                        && person.roles().contains(requiredRole)
                    )
                    .findFirst()
                    .orElseThrow(() ->
                        new IllegalStateException(
                            "No eligible candidate for role " + requiredRole
                        )
                    );

                team.add(candidate);
                selected.add(candidate.id());
            }

            while (team.size() < project.minimumTeamSize()) {
                Set<String> missing = missingSkills(project, team);

                Candidate candidate = eligible.stream()
                    .filter(person -> !selected.contains(person.id()))
                    .max(
                        Comparator.comparingInt(
                            person -> skillCoverage(person, missing)
                        ).thenComparingDouble(
                            Candidate::experienceYears
                        )
                    )
                    .orElseThrow(() ->
                        new IllegalStateException(
                            "Insufficient candidates for minimum team size."
                        )
                    );

                team.add(candidate);
                selected.add(candidate.id());
            }

            while (team.size() < project.maximumTeamSize()) {
                Set<String> before = missingSkills(project, team);

                Optional<Candidate> optional = eligible.stream()
                    .filter(person -> !selected.contains(person.id()))
                    .filter(person -> skillCoverage(person, before) > 0)
                    .max(
                        Comparator.comparingInt(
                            person -> skillCoverage(person, before)
                        ).thenComparingDouble(
                            Candidate::experienceYears
                        )
                    );

                if (optional.isEmpty()) break;

                Candidate candidate = optional.get();
                team.add(candidate);
                selected.add(candidate.id());

                Set<String> after = missingSkills(project, team);

                if (after.size() >= before.size()) {
                    team.remove(candidate);
                    selected.remove(candidate.id());
                    break;
                }
            }

            List<String> reasons = new ArrayList<>();

            for (TeamPolicy policy : policies) {
                if (!policy.accepts(project, team)) {
                    reasons.add(policy.rejectionReason(project, team));
                }
            }

            TeamState state = reasons.isEmpty()
                ? TeamState.VALIDATED
                : TeamState.REJECTED;

            return new FormationDecision(
                state,
                team.stream().map(Candidate::name).toList(),
                missingRoles(project, team),
                missingSkills(project, team),
                List.copyOf(reasons)
            );
        }

        private static double score(Candidate candidate, Project project) {
            long skillMatches = candidate.skills().stream()
                .filter(project.requiredSkills()::contains)
                .count();

            long roleMatches = candidate.roles().stream()
                .filter(project.requiredRoles()::contains)
                .count();

            double availability = switch (candidate.availability()) {
                case AVAILABLE -> 3.0;
                case PARTIAL -> 1.0;
                case UNAVAILABLE -> -100.0;
            };

            return skillMatches * 4.0
                + roleMatches * 6.0
                + Math.min(candidate.experienceYears(), 10.0) * 0.25
                + availability;
        }

        private static int skillCoverage(
            Candidate candidate,
            Set<String> missing
        ) {
            return (int) candidate.skills().stream()
                .filter(missing::contains)
                .count();
        }
    }

    private static Set<Role> missingRoles(
        Project project,
        List<Candidate> team
    ) {
        Set<Role> covered = team.stream()
            .flatMap(candidate -> candidate.roles().stream())
            .collect(Collectors.toSet());

        return project.requiredRoles().stream()
            .filter(role -> !covered.contains(role))
            .collect(Collectors.toCollection(TreeSet::new));
    }

    private static Set<String> missingSkills(
        Project project,
        List<Candidate> team
    ) {
        Set<String> covered = team.stream()
            .flatMap(candidate -> candidate.skills().stream())
            .collect(Collectors.toSet());

        return project.requiredSkills().stream()
            .filter(skill -> !covered.contains(skill))
            .collect(Collectors.toCollection(TreeSet::new));
    }

    public static void main(String[] args) {
        List<Candidate> candidates = List.of(
            new Candidate(
                "C001",
                "Aarav",
                Set.of("roadmapping", "stakeholder-management", "analytics"),
                Set.of(Role.PRODUCT_MANAGER),
                7,
                Availability.AVAILABLE
            ),
            new Candidate(
                "C002",
                "Meera",
                Set.of("architecture", "python", "postgresql", "security"),
                Set.of(Role.TECH_LEAD, Role.BACKEND),
                9,
                Availability.AVAILABLE
            ),
            new Candidate(
                "C003",
                "Kabir",
                Set.of("python", "fastapi", "postgresql", "testing"),
                Set.of(Role.BACKEND),
                5,
                Availability.AVAILABLE
            ),
            new Candidate(
                "C004",
                "Diya",
                Set.of("javascript", "react", "accessibility", "css"),
                Set.of(Role.FRONTEND, Role.UX),
                4,
                Availability.AVAILABLE
            ),
            new Candidate(
                "C005",
                "Rohan",
                Set.of("pytest", "automation", "testing", "quality"),
                Set.of(Role.QA),
                6,
                Availability.AVAILABLE
            ),
            new Candidate(
                "C006",
                "Ishita",
                Set.of("docker", "kubernetes", "ci-cd", "linux"),
                Set.of(Role.DEVOPS),
                6,
                Availability.PARTIAL
            ),
            new Candidate(
                "C008",
                "Nisha",
                Set.of("threat-modeling", "security", "iam", "python"),
                Set.of(Role.SECURITY),
                7,
                Availability.AVAILABLE
            )
        );

        Project project = new Project(
            "P001",
            "Secure Operations Analytics Platform",
            Set.of(
                "roadmapping",
                "architecture",
                "python",
                "postgresql",
                "javascript",
                "testing",
                "docker",
                "security"
            ),
            Set.of(
                Role.PRODUCT_MANAGER,
                Role.TECH_LEAD,
                Role.BACKEND,
                Role.FRONTEND,
                Role.QA,
                Role.DEVOPS,
                Role.SECURITY
            ),
            7,
            8,
            true
        );

        TeamFormationService service = new TeamFormationService(
            candidates,
            List.of(
                new MinimumCoveragePolicy(),
                new SecurityPolicy()
            )
        );

        FormationDecision decision = service.form(project);

        System.out.println("Project: " + project.name());
        System.out.println("State: " + decision.state());
        System.out.println("Members: " + decision.selectedMembers());
        System.out.println("Missing roles: " + decision.missingRoles());
        System.out.println("Missing skills: " + decision.missingSkills());

        if (decision.reasons().isEmpty()) {
            System.out.println("Policy validation: PASSED");
        } else {
            System.out.println("Policy validation: REJECTED");
            decision.reasons().forEach(reason ->
                System.out.println(" - " + reason)
            );
        }
    }
}
