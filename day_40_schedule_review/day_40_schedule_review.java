import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

public class ScheduleReviewEnterprise {

    enum TaskStatus {
        PLANNED,
        IN_PROGRESS,
        COMPLETE,
        BLOCKED
    }

    enum ReviewDecision {
        ACCEPT,
        REVISE,
        ESCALATE
    }

    record Task(
        String id,
        String name,
        LocalDate start,
        LocalDate end,
        String owner,
        List<String> dependencies,
        double plannedHours,
        double progress,
        TaskStatus status,
        String priority
    ) {
        Task {
            Objects.requireNonNull(id);
            Objects.requireNonNull(name);
            Objects.requireNonNull(start);
            Objects.requireNonNull(end);
            Objects.requireNonNull(owner);
            Objects.requireNonNull(dependencies);
            Objects.requireNonNull(status);
            Objects.requireNonNull(priority);

            if (id.isBlank() || name.isBlank() || owner.isBlank()) {
                throw new IllegalArgumentException("Task identity fields cannot be blank.");
            }

            if (end.isBefore(start)) {
                throw new IllegalArgumentException(
                    "Task " + id + " ends before it starts."
                );
            }

            if (plannedHours < 0) {
                throw new IllegalArgumentException("Planned hours cannot be negative.");
            }

            if (progress < 0 || progress > 100) {
                throw new IllegalArgumentException(
                    "Progress must be between 0 and 100."
                );
            }

            dependencies = List.copyOf(dependencies);
        }

        long durationDays() {
            return ChronoUnit.DAYS.between(start, end) + 1;
        }

        boolean overlaps(Task other) {
            return !end.isBefore(other.start) && !other.end.isBefore(start);
        }
    }

    record DependencyFinding(
        String taskId,
        String dependencyId,
        String message
    ) {}

    record ResourceConflict(
        String owner,
        String firstTask,
        String secondTask,
        LocalDate start,
        LocalDate end
    ) {}

    record CapacityFinding(
        String owner,
        double plannedHours,
        double capacity,
        double excess
    ) {}

    record ReviewEvidence(
        List<DependencyFinding> dependencyFindings,
        List<ResourceConflict> resourceConflicts,
        List<CapacityFinding> capacityFindings,
        Optional<List<String>> dependencyCycle,
        List<String> criticalPath
    ) {}

    interface ReviewRule {
        Optional<String> validate(ReviewEvidence evidence);
    }

    static final class DependencyRule implements ReviewRule {
        @Override
        public Optional<String> validate(ReviewEvidence evidence) {
            if (!evidence.dependencyFindings().isEmpty()) {
                return Optional.of("Dependency validation failed.");
            }
            return Optional.empty();
        }
    }

    static final class ResourceRule implements ReviewRule {
        @Override
        public Optional<String> validate(ReviewEvidence evidence) {
            if (!evidence.resourceConflicts().isEmpty()) {
                return Optional.of("Resource overlap exists.");
            }
            return Optional.empty();
        }
    }

    static final class CapacityRule implements ReviewRule {
        @Override
        public Optional<String> validate(ReviewEvidence evidence) {
            if (!evidence.capacityFindings().isEmpty()) {
                return Optional.of("Resource capacity is exceeded.");
            }
            return Optional.empty();
        }
    }

    static final class CycleRule implements ReviewRule {
        @Override
        public Optional<String> validate(ReviewEvidence evidence) {
            if (evidence.dependencyCycle().isPresent()) {
                return Optional.of(
                    "Dependency cycle prevents reliable schedule evaluation."
                );
            }
            return Optional.empty();
        }
    }

    static final class ScheduleRepository {
        private final Map<String, Task> tasks = new LinkedHashMap<>();

        void add(Task task) {
            if (tasks.containsKey(task.id())) {
                throw new IllegalArgumentException(
                    "Duplicate task ID: " + task.id()
                );
            }
            tasks.put(task.id(), task);
        }

        Task require(String id) {
            Task task = tasks.get(id);
            if (task == null) {
                throw new IllegalArgumentException(
                    "Unknown task: " + id
                );
            }
            return task;
        }

        List<Task> all() {
            return List.copyOf(tasks.values());
        }

        boolean contains(String id) {
            return tasks.containsKey(id);
        }
    }

    static final class ScheduleAnalysisService {
        private final ScheduleRepository repository;

        ScheduleAnalysisService(ScheduleRepository repository) {
            this.repository = repository;
        }

        List<DependencyFinding> dependencyFindings() {
            List<DependencyFinding> findings = new ArrayList<>();

            for (Task task : repository.all()) {
                for (String dependencyId : task.dependencies()) {
                    if (!repository.contains(dependencyId)) {
                        findings.add(new DependencyFinding(
                            task.id(),
                            dependencyId,
                            "Referenced dependency does not exist."
                        ));
                        continue;
                    }

                    Task dependency = repository.require(dependencyId);

                    if (dependency.end().isAfter(task.start())) {
                        findings.add(new DependencyFinding(
                            task.id(),
                            dependencyId,
                            "Dependency ends after dependent task starts."
                        ));
                    }
                }
            }

            return findings;
        }

        Optional<List<String>> findCycle() {
            Set<String> visiting = new HashSet<>();
            Set<String> visited = new HashSet<>();
            Deque<String> path = new ArrayDeque<>();

            for (Task task : repository.all()) {
                Optional<List<String>> result =
                    visit(task.id(), visiting, visited, path);

                if (result.isPresent()) {
                    return result;
                }
            }

            return Optional.empty();
        }

        private Optional<List<String>> visit(
            String id,
            Set<String> visiting,
            Set<String> visited,
            Deque<String> path
        ) {
            if (visiting.contains(id)) {
                List<String> cycle = new ArrayList<>();
                boolean collecting = false;

                for (String pathId : path) {
                    if (pathId.equals(id)) {
                        collecting = true;
                    }
                    if (collecting) {
                        cycle.add(pathId);
                    }
                }

                cycle.add(id);
                return Optional.of(cycle);
            }

            if (visited.contains(id)) {
                return Optional.empty();
            }

            visiting.add(id);
            path.addLast(id);

            Task task = repository.require(id);

            for (String dependency : task.dependencies()) {
                if (repository.contains(dependency)) {
                    Optional<List<String>> result =
                        visit(dependency, visiting, visited, path);

                    if (result.isPresent()) {
                        return result;
                    }
                }
            }

            path.removeLast();
            visiting.remove(id);
            visited.add(id);

            return Optional.empty();
        }

        List<ResourceConflict> resourceConflicts() {
            Map<String, List<Task>> byOwner = new HashMap<>();

            for (Task task : repository.all()) {
                byOwner.computeIfAbsent(task.owner(), key -> new ArrayList<>())
                    .add(task);
            }

            List<ResourceConflict> conflicts = new ArrayList<>();

            for (Map.Entry<String, List<Task>> entry : byOwner.entrySet()) {
                List<Task> ownerTasks = entry.getValue();

                ownerTasks.sort(Comparator.comparing(Task::start));

                for (int i = 0; i < ownerTasks.size(); i++) {
                    for (int j = i + 1; j < ownerTasks.size(); j++) {
                        Task first = ownerTasks.get(i);
                        Task second = ownerTasks.get(j);

                        if (second.start().isAfter(first.end())) {
                            break;
                        }

                        if (first.overlaps(second)) {
                            LocalDate overlapStart =
                                first.start().isAfter(second.start())
                                    ? first.start()
                                    : second.start();

                            LocalDate overlapEnd =
                                first.end().isBefore(second.end())
                                    ? first.end()
                                    : second.end();

                            conflicts.add(new ResourceConflict(
                                entry.getKey(),
                                first.id(),
                                second.id(),
                                overlapStart,
                                overlapEnd
                            ));
                        }
                    }
                }
            }

            return conflicts;
        }

        List<CapacityFinding> capacityFindings(
            Map<String, Double> capacity
        ) {
            Map<String, Double> workload = new HashMap<>();

            for (Task task : repository.all()) {
                workload.merge(
                    task.owner(),
                    task.plannedHours(),
                    Double::sum
                );
            }

            List<CapacityFinding> findings = new ArrayList<>();

            for (Map.Entry<String, Double> entry : workload.entrySet()) {
                Double limit = capacity.get(entry.getKey());

                if (limit != null && entry.getValue() > limit) {
                    findings.add(new CapacityFinding(
                        entry.getKey(),
                        entry.getValue(),
                        limit,
                        entry.getValue() - limit
                    ));
                }
            }

            return findings;
        }

        List<String> criticalPath() {
            if (findCycle().isPresent()) {
                throw new IllegalStateException(
                    "Cannot calculate critical path for a cyclic schedule."
                );
            }

            Map<String, PathResult> memo = new HashMap<>();
            PathResult best = new PathResult(0, List.of());

            for (Task task : repository.all()) {
                PathResult result = longest(task.id(), memo);

                if (result.duration() > best.duration()) {
                    best = result;
                }
            }

            return best.path();
        }

        private PathResult longest(
            String taskId,
            Map<String, PathResult> memo
        ) {
            if (memo.containsKey(taskId)) {
                return memo.get(taskId);
            }

            Task task = repository.require(taskId);

            if (task.dependencies().isEmpty()) {
                PathResult result = new PathResult(
                    task.durationDays(),
                    List.of(taskId)
                );
                memo.put(taskId, result);
                return result;
            }

            PathResult best = new PathResult(0, List.of());

            for (String dependency : task.dependencies()) {
                if (!repository.contains(dependency)) {
                    continue;
                }

                PathResult candidate = longest(dependency, memo);

                if (candidate.duration() > best.duration()) {
                    best = candidate;
                }
            }

            List<String> path = new ArrayList<>(best.path());
            path.add(taskId);

            PathResult result = new PathResult(
                best.duration() + task.durationDays(),
                List.copyOf(path)
            );

            memo.put(taskId, result);
            return result;
        }
    }

    record PathResult(long duration, List<String> path) {}

    static final class ScheduleReviewService {
        private final List<ReviewRule> rules;

        ScheduleReviewService(List<ReviewRule> rules) {
            this.rules = List.copyOf(rules);
        }

        ReviewDecision decide(ReviewEvidence evidence) {
            if (evidence.dependencyCycle().isPresent()) {
                return ReviewDecision.ESCALATE;
            }

            long failures = rules.stream()
                .map(rule -> rule.validate(evidence))
                .filter(Optional::isPresent)
                .count();

            if (failures == 0) {
                return ReviewDecision.ACCEPT;
            }

            return ReviewDecision.REVISE;
        }

        List<String> findings(ReviewEvidence evidence) {
            return rules.stream()
                .map(rule -> rule.validate(evidence))
                .filter(Optional::isPresent)
                .map(Optional::get)
                .toList();
        }
    }

    static ScheduleRepository createSchedule() {
        ScheduleRepository repository = new ScheduleRepository();

        repository.add(new Task(
            "PLAN",
            "Planning baseline",
            LocalDate.of(2026, 10, 1),
            LocalDate.of(2026, 10, 3),
            "Asha",
            List.of(),
            18,
            100,
            TaskStatus.COMPLETE,
            "high"
        ));

        repository.add(new Task(
            "DESIGN",
            "Architecture design",
            LocalDate.of(2026, 10, 4),
            LocalDate.of(2026, 10, 6),
            "Ravi",
            List.of("PLAN"),
            20,
            100,
            TaskStatus.COMPLETE,
            "high"
        ));

        repository.add(new Task(
            "BUILD",
            "Service implementation",
            LocalDate.of(2026, 10, 7),
            LocalDate.of(2026, 10, 12),
            "Ravi",
            List.of("DESIGN"),
            36,
            55,
            TaskStatus.IN_PROGRESS,
            "high"
        ));

        repository.add(new Task(
            "DATA",
            "Schedule data validation",
            LocalDate.of(2026, 10, 8),
            LocalDate.of(2026, 10, 11),
            "Meera",
            List.of("DESIGN"),
            24,
            70,
            TaskStatus.IN_PROGRESS,
            "normal"
        ));

        repository.add(new Task(
            "TEST",
            "Integrated testing",
            LocalDate.of(2026, 10, 13),
            LocalDate.of(2026, 10, 16),
            "Asha",
            List.of("BUILD", "DATA"),
            28,
            0,
            TaskStatus.PLANNED,
            "high"
        ));

        repository.add(new Task(
            "RELEASE",
            "Production release",
            LocalDate.of(2026, 10, 19),
            LocalDate.of(2026, 10, 19),
            "Asha",
            List.of("TEST"),
            8,
            0,
            TaskStatus.PLANNED,
            "high"
        ));

        return repository;
    }

    static ReviewEvidence buildEvidence(
        ScheduleAnalysisService analysis,
        Map<String, Double> capacity
    ) {
        return new ReviewEvidence(
            analysis.dependencyFindings(),
            analysis.resourceConflicts(),
            analysis.capacityFindings(capacity),
            analysis.findCycle(),
            analysis.criticalPath()
        );
    }

    static void printReport(
        ReviewEvidence evidence,
        ReviewDecision decision,
        List<String> policyFindings
    ) {
        System.out.println("SCHEDULE REVIEW");
        System.out.println("===============");
        System.out.println("Decision: " + decision);
        System.out.println(
            "Critical path: " +
            String.join(" -> ", evidence.criticalPath())
        );

        System.out.println("\nDependency findings:");
        if (evidence.dependencyFindings().isEmpty()) {
            System.out.println("  none");
        } else {
            evidence.dependencyFindings().forEach(finding ->
                System.out.println(
                    "  " + finding.taskId() + " -> " +
                    finding.dependencyId() + ": " +
                    finding.message()
                )
            );
        }

        System.out.println("\nResource conflicts:");
        if (evidence.resourceConflicts().isEmpty()) {
            System.out.println("  none");
        } else {
            evidence.resourceConflicts().forEach(conflict ->
                System.out.println(
                    "  " + conflict.owner() + ": " +
                    conflict.firstTask() + " overlaps " +
                    conflict.secondTask() + " from " +
                    conflict.start() + " to " +
                    conflict.end()
                )
            );
        }

        System.out.println("\nCapacity findings:");
        if (evidence.capacityFindings().isEmpty()) {
            System.out.println("  none");
        } else {
            evidence.capacityFindings().forEach(finding ->
                System.out.printf(
                    "  %s: %.1f planned, %.1f capacity, %.1f excess%n",
                    finding.owner(),
                    finding.plannedHours(),
                    finding.capacity(),
                    finding.excess()
                )
            );
        }

        System.out.println("\nPolicy findings:");
        if (policyFindings.isEmpty()) {
            System.out.println("  none");
        } else {
            policyFindings.forEach(finding ->
                System.out.println("  " + finding)
            );
        }

        evidence.dependencyCycle().ifPresent(cycle ->
            System.out.println(
                "\nDependency cycle: " + String.join(" -> ", cycle)
            )
        );
    }

    public static void main(String[] args) {
        ScheduleRepository repository = createSchedule();

        ScheduleAnalysisService analysis =
            new ScheduleAnalysisService(repository);

        Map<String, Double> capacity = Map.of(
            "Asha", 70.0,
            "Ravi", 65.0,
            "Meera", 40.0
        );

        ReviewEvidence evidence = buildEvidence(analysis, capacity);

        ScheduleReviewService reviewService =
            new ScheduleReviewService(List.of(
                new CycleRule(),
                new DependencyRule(),
                new ResourceRule(),
                new CapacityRule()
            ));

        ReviewDecision decision = reviewService.decide(evidence);
        List<String> policyFindings = reviewService.findings(evidence);

        printReport(evidence, decision, policyFindings);

        System.out.println("\nTask state model:");
        repository.all().forEach(task ->
            System.out.printf(
                "%s | %s | %s | %s | %.0f%%%n",
                task.id(),
                task.name(),
                task.status(),
                task.priority(),
                task.progress()
            )
        );
    }
}
