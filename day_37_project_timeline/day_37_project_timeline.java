import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

public class ProjectTimelineApp {

    enum Priority {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }

    enum TaskState {
        PLANNED,
        IN_PROGRESS,
        COMPLETED,
        BLOCKED,
        OVERDUE
    }

    record Milestone(
        String name,
        LocalDate dueDate,
        String description,
        boolean completed
    ) {
        Milestone {
            Objects.requireNonNull(name);
            Objects.requireNonNull(dueDate);
            if (name.isBlank()) {
                throw new IllegalArgumentException("Milestone name cannot be blank.");
            }
        }
    }

    static final class ProjectTask {
        private final String id;
        private final String name;
        private final LocalDate start;
        private final LocalDate end;
        private final String owner;
        private final Set<String> dependencies;
        private final Priority priority;
        private int progress;

        ProjectTask(
            String id,
            String name,
            LocalDate start,
            LocalDate end,
            String owner,
            Set<String> dependencies,
            Priority priority,
            int progress
        ) {
            this.id = requireText(id, "Task ID");
            this.name = requireText(name, "Task name");
            this.start = Objects.requireNonNull(start);
            this.end = Objects.requireNonNull(end);
            this.owner = requireText(owner, "Owner");
            this.dependencies = new HashSet<>(dependencies);
            this.priority = Objects.requireNonNull(priority);
            setProgress(progress);

            if (end.isBefore(start)) {
                throw new IllegalArgumentException(
                    "Task " + id + " ends before it starts."
                );
            }

            if (dependencies.contains(id)) {
                throw new IllegalArgumentException(
                    "Task " + id + " cannot depend on itself."
                );
            }
        }

        private static String requireText(String value, String field) {
            if (value == null || value.isBlank()) {
                throw new IllegalArgumentException(field + " is required.");
            }
            return value;
        }

        public void setProgress(int progress) {
            if (progress < 0 || progress > 100) {
                throw new IllegalArgumentException(
                    "Progress must be between 0 and 100."
                );
            }
            this.progress = progress;
        }

        public String id() {
            return id;
        }

        public String name() {
            return name;
        }

        public LocalDate start() {
            return start;
        }

        public LocalDate end() {
            return end;
        }

        public String owner() {
            return owner;
        }

        public Set<String> dependencies() {
            return Collections.unmodifiableSet(dependencies);
        }

        public Priority priority() {
            return priority;
        }

        public int progress() {
            return progress;
        }

        public long duration() {
            return ChronoUnit.DAYS.between(start, end) + 1;
        }

        public TaskState state(LocalDate asOf) {
            if (progress == 100) {
                return TaskState.COMPLETED;
            }

            if (end.isBefore(asOf)) {
                return TaskState.OVERDUE;
            }

            if (start.isAfter(asOf)) {
                return TaskState.PLANNED;
            }

            if (progress == 0) {
                return TaskState.BLOCKED;
            }

            return TaskState.IN_PROGRESS;
        }
    }

    static final class Timeline {
        private final String projectName;
        private final Map<String, ProjectTask> tasks = new HashMap<>();
        private final List<Milestone> milestones = new ArrayList<>();

        Timeline(String projectName) {
            this.projectName = Objects.requireNonNull(projectName);
        }

        void addTask(ProjectTask task) {
            if (tasks.putIfAbsent(task.id(), task) != null) {
                throw new IllegalArgumentException(
                    "Duplicate task ID: " + task.id()
                );
            }
        }

        void addMilestone(Milestone milestone) {
            milestones.add(milestone);
        }

        List<String> validateDependencies() {
            List<String> errors = new ArrayList<>();

            for (ProjectTask task : tasks.values()) {
                for (String dependencyId : task.dependencies()) {
                    ProjectTask dependency = tasks.get(dependencyId);

                    if (dependency == null) {
                        errors.add(
                            task.id() + " references missing dependency " +
                            dependencyId
                        );
                    } else if (!dependency.end().isBefore(task.start())) {
                        errors.add(
                            task.id() + " starts before dependency " +
                            dependency.id() + " finishes"
                        );
                    }
                }
            }

            return errors;
        }

        boolean containsCycle() {
            Set<String> visiting = new HashSet<>();
            Set<String> visited = new HashSet<>();

            for (String taskId : tasks.keySet()) {
                if (visit(taskId, visiting, visited)) {
                    return true;
                }
            }

            return false;
        }

        private boolean visit(
            String taskId,
            Set<String> visiting,
            Set<String> visited
        ) {
            if (visiting.contains(taskId)) {
                return true;
            }

            if (visited.contains(taskId)) {
                return false;
            }

            visiting.add(taskId);

            ProjectTask task = tasks.get(taskId);

            if (task != null) {
                for (String dependency : task.dependencies()) {
                    if (tasks.containsKey(dependency) &&
                        visit(dependency, visiting, visited)) {
                        return true;
                    }
                }
            }

            visiting.remove(taskId);
            visited.add(taskId);
            return false;
        }

        List<String> criticalPath() {
            if (!validateDependencies().isEmpty()) {
                throw new IllegalStateException(
                    "Dependency errors prevent critical-path calculation."
                );
            }

            if (containsCycle()) {
                throw new IllegalStateException(
                    "Cyclic dependencies prevent critical-path calculation."
                );
            }

            List<ProjectTask> ordered = new ArrayList<>(tasks.values());

            ordered.sort(
                (left, right) -> left.end().compareTo(right.end())
            );

            Map<String, Long> longestFinish = new HashMap<>();
            Map<String, String> predecessor = new HashMap<>();

            for (ProjectTask task : ordered) {
                long bestFinish = 0;
                String bestDependency = null;

                for (String dependency : task.dependencies()) {
                    long candidate = longestFinish.getOrDefault(dependency, 0L);

                    if (candidate > bestFinish) {
                        bestFinish = candidate;
                        bestDependency = dependency;
                    }
                }

                longestFinish.put(
                    task.id(),
                    bestFinish + task.duration()
                );

                predecessor.put(task.id(), bestDependency);
            }

            String finalTask = longestFinish.entrySet()
                .stream()
                .max(Map.Entry.comparingByValue())
                .map(Map.Entry::getKey)
                .orElseThrow();

            List<String> path = new ArrayList<>();

            while (finalTask != null) {
                path.add(finalTask);
                finalTask = predecessor.get(finalTask);
            }

            Collections.reverse(path);
            return path;
        }

        double weightedProgress() {
            long totalDuration = 0;
            long weightedProgress = 0;

            for (ProjectTask task : tasks.values()) {
                totalDuration += task.duration();
                weightedProgress +=
                    task.duration() * task.progress();
            }

            if (totalDuration == 0) {
                return 0;
            }

            return (double) weightedProgress / totalDuration;
        }

        void printState(LocalDate asOf) {
            System.out.println("\nENTERPRISE PROJECT TIMELINE");
            System.out.println(projectName);

            tasks.values()
                .stream()
                .sorted((a, b) -> a.start().compareTo(b.start()))
                .forEach(task ->
                    System.out.printf(
                        "%s | %-30s | %s -> %s | %-11s | %3d%%%n",
                        task.id(),
                        task.name(),
                        task.start(),
                        task.end(),
                        task.state(asOf),
                        task.progress()
                    )
                );
        }

        void printMilestones(LocalDate asOf) {
            System.out.println("\nMILESTONES");

            milestones.stream()
                .sorted((a, b) -> a.dueDate().compareTo(b.dueDate()))
                .forEach(milestone -> {
                    String status;

                    if (milestone.completed()) {
                        status = "COMPLETED";
                    } else if (milestone.dueDate().isBefore(asOf)) {
                        status = "OVERDUE";
                    } else if (
                        !milestone.dueDate().isAfter(asOf.plusDays(7))
                    ) {
                        status = "DUE_SOON";
                    } else {
                        status = "UPCOMING";
                    }

                    System.out.printf(
                        "%s | %s | %s%n",
                        milestone.dueDate(),
                        status,
                        milestone.name()
                    );
                });
        }

        void printRisks(LocalDate asOf) {
            System.out.println("\nTIMELINE RISKS");

            boolean foundRisk = false;

            for (ProjectTask task : tasks.values()) {
                if (
                    task.state(asOf) == TaskState.OVERDUE ||
                    (EnumSet.of(Priority.HIGH, Priority.CRITICAL)
                        .contains(task.priority()) &&
                     task.progress() < 50)
                ) {
                    foundRisk = true;

                    System.out.printf(
                        "%s | priority=%s | progress=%d%% | state=%s%n",
                        task.id(),
                        task.priority(),
                        task.progress(),
                        task.state(asOf)
                    );
                }
            }

            if (!foundRisk) {
                System.out.println("No timeline risks detected.");
            }
        }
    }

    public static void main(String[] args) {
        Timeline timeline =
            new Timeline("Public-Sector Operations Analytics Platform");

        timeline.addTask(new ProjectTask(
            "T01",
            "Business requirements",
            LocalDate.of(2026, 10, 12),
            LocalDate.of(2026, 10, 19),
            "Business Analyst",
            Set.of(),
            Priority.HIGH,
            100
        ));

        timeline.addTask(new ProjectTask(
            "T02",
            "Architecture design",
            LocalDate.of(2026, 10, 20),
            LocalDate.of(2026, 10, 28),
            "Solution Architect",
            Set.of("T01"),
            Priority.HIGH,
            75
        ));

        timeline.addTask(new ProjectTask(
            "T03",
            "Data integration",
            LocalDate.of(2026, 10, 29),
            LocalDate.of(2026, 11, 10),
            "Data Engineering",
            Set.of("T02"),
            Priority.CRITICAL,
            35
        ));

        timeline.addTask(new ProjectTask(
            "T04",
            "Application validation",
            LocalDate.of(2026, 11, 11),
            LocalDate.of(2026, 11, 17),
            "QA Team",
            Set.of("T03"),
            Priority.HIGH,
            0
        ));

        timeline.addTask(new ProjectTask(
            "T05",
            "Operational deployment",
            LocalDate.of(2026, 11, 18),
            LocalDate.of(2026, 11, 20),
            "Release Manager",
            Set.of("T04"),
            Priority.CRITICAL,
            0
        ));

        timeline.addMilestone(new Milestone(
            "Requirements approved",
            LocalDate.of(2026, 10, 19),
            "Business requirements baseline",
            true
        ));

        timeline.addMilestone(new Milestone(
            "Production deployment",
            LocalDate.of(2026, 11, 20),
            "Operational handover",
            false
        ));

        LocalDate asOf = LocalDate.of(2026, 11, 12);

        timeline.printState(asOf);
        timeline.printMilestones(asOf);
        timeline.printRisks(asOf);

        System.out.println("\nDEPENDENCY VALIDATION");
        List<String> dependencyErrors = timeline.validateDependencies();

        if (dependencyErrors.isEmpty()) {
            System.out.println("All dependencies are valid.");
        } else {
            dependencyErrors.forEach(System.out::println);
        }

        System.out.println("\nCRITICAL PATH");
        System.out.println(String.join(" -> ", timeline.criticalPath()));

        System.out.printf(
            "Weighted progress: %.1f%%%n",
            timeline.weightedProgress()
        );

        try {
            new ProjectTask(
                "INVALID",
                "Invalid progress example",
                LocalDate.of(2026, 12, 1),
                LocalDate.of(2026, 12, 5),
                "Tester",
                Set.of(),
                Priority.LOW,
                120
            );
        } catch (IllegalArgumentException exception) {
            System.out.println(
                "\nValidation rejected invalid task: " +
                exception.getMessage()
            );
        }
    }
}
