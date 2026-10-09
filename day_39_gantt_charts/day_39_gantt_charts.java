import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Queue;
import java.util.Set;

public class GanttProjectDemo {

    enum TaskStatus {
        NOT_STARTED,
        IN_PROGRESS,
        COMPLETED,
        BLOCKED
    }

    record Task(
        String id,
        String name,
        LocalDate start,
        LocalDate end,
        List<String> dependencies,
        String resource,
        int progress,
        boolean milestone
    ) {
        Task {
            Objects.requireNonNull(id);
            Objects.requireNonNull(name);
            Objects.requireNonNull(start);
            Objects.requireNonNull(end);
            Objects.requireNonNull(dependencies);

            if (id.isBlank() || name.isBlank()) {
                throw new IllegalArgumentException("Task ID and name are required.");
            }

            if (end.isBefore(start)) {
                throw new IllegalArgumentException(
                    "Task end date cannot precede start date."
                );
            }

            if (progress < 0 || progress > 100) {
                throw new IllegalArgumentException(
                    "Progress must be between 0 and 100."
                );
            }

            if (milestone && !start.equals(end)) {
                throw new IllegalArgumentException(
                    "A milestone must occupy a single date."
                );
            }

            dependencies = List.copyOf(dependencies);
        }

        long duration() {
            return ChronoUnit.DAYS.between(start, end) + 1;
        }

        TaskStatus status() {
            if (progress == 100) {
                return TaskStatus.COMPLETED;
            }

            if (progress == 0) {
                return TaskStatus.NOT_STARTED;
            }

            return TaskStatus.IN_PROGRESS;
        }
    }

    static final class Schedule {
        private final String name;
        private final Map<String, Task> tasks = new HashMap<>();

        Schedule(String name) {
            this.name = name;
        }

        void addTask(Task task) {
            if (tasks.containsKey(task.id())) {
                throw new IllegalArgumentException(
                    "Duplicate task: " + task.id()
                );
            }

            tasks.put(task.id(), task);
        }

        Task task(String id) {
            Task task = tasks.get(id);

            if (task == null) {
                throw new IllegalArgumentException(
                    "Unknown task: " + id
                );
            }

            return task;
        }

        void validate() {
            topologicalOrder();

            for (Task task : tasks.values()) {
                for (String dependencyId : task.dependencies()) {
                    Task dependency = task(dependencyId);

                    if (!dependency.end().isBefore(task.start())) {
                        throw new IllegalStateException(
                            "Dependency violation: " +
                            dependency.id() + " must finish before " +
                            task.id() + " starts."
                        );
                    }
                }
            }
        }

        List<String> topologicalOrder() {
            Map<String, Integer> indegree = new HashMap<>();
            Map<String, List<String>> successors = new HashMap<>();

            for (String id : tasks.keySet()) {
                indegree.put(id, 0);
                successors.put(id, new ArrayList<>());
            }

            for (Task task : tasks.values()) {
                for (String dependency : task.dependencies()) {
                    task(dependency);

                    indegree.put(
                        task.id(),
                        indegree.get(task.id()) + 1
                    );

                    successors.get(dependency).add(task.id());
                }
            }

            Queue<String> ready = new ArrayDeque<>();

            for (Map.Entry<String, Integer> entry : indegree.entrySet()) {
                if (entry.getValue() == 0) {
                    ready.add(entry.getKey());
                }
            }

            List<String> result = new ArrayList<>();

            while (!ready.isEmpty()) {
                String current = ready.remove();
                result.add(current);

                for (String successor : successors.get(current)) {
                    int remaining = indegree.get(successor) - 1;
                    indegree.put(successor, remaining);

                    if (remaining == 0) {
                        ready.add(successor);
                    }
                }
            }

            if (result.size() != tasks.size()) {
                throw new IllegalStateException(
                    "Circular dependency detected."
                );
            }

            return result;
        }

        List<String> criticalPath() {
            List<String> order = topologicalOrder();
            Map<String, Long> finish = new HashMap<>();
            Map<String, String> previous = new HashMap<>();

            for (String id : order) {
                Task current = task(id);

                if (current.dependencies().isEmpty()) {
                    finish.put(id, current.duration());
                    previous.put(id, null);
                    continue;
                }

                String best = current.dependencies().stream()
                    .max(Comparator.comparingLong(finish::get))
                    .orElseThrow();

                finish.put(
                    id,
                    finish.get(best) + current.duration()
                );

                previous.put(id, best);
            }

            String last = order.stream()
                .max(Comparator.comparingLong(finish::get))
                .orElseThrow();

            List<String> path = new ArrayList<>();

            while (last != null) {
                path.add(0, last);
                last = previous.get(last);
            }

            return path;
        }

        Map<String, List<String>> resourceConflicts() {
            Map<String, List<Task>> resources = new HashMap<>();

            for (Task task : tasks.values()) {
                if (task.resource() != null && !task.resource().isBlank()) {
                    resources
                        .computeIfAbsent(task.resource(), key -> new ArrayList<>())
                        .add(task);
                }
            }

            Map<String, List<String>> conflicts = new HashMap<>();

            for (Map.Entry<String, List<Task>> entry : resources.entrySet()) {
                List<Task> resourceTasks = entry.getValue();

                resourceTasks.sort(
                    Comparator.comparing(Task::start)
                );

                for (int i = 0; i < resourceTasks.size(); i++) {
                    for (int j = i + 1; j < resourceTasks.size(); j++) {
                        Task first = resourceTasks.get(i);
                        Task second = resourceTasks.get(j);

                        if (second.start().isAfter(first.end())) {
                            break;
                        }

                        conflicts
                            .computeIfAbsent(
                                entry.getKey(),
                                key -> new ArrayList<>()
                            )
                            .add(first.id() + " overlaps " + second.id());
                    }
                }
            }

            return conflicts;
        }

        void render() {
            System.out.println();
            System.out.println("GANTT CHART: " + name);
            System.out.println();

            tasks.values().stream()
                .sorted(Comparator.comparing(Task::start))
                .forEach(task -> {
                    StringBuilder bar = new StringBuilder();

                    if (task.milestone()) {
                        bar.append("*");
                    } else {
                        int completed =
                            (int) Math.round(
                                task.duration() * task.progress() / 100.0
                            );

                        bar.append("|".repeat(
                            Math.min(completed, (int) task.duration())
                        ));

                        bar.append(".".repeat(
                            Math.max(
                                0,
                                (int) task.duration() - completed
                            )
                        ));
                    }

                    System.out.printf(
                        "%-28s %s  %s -> %s  %3d%%%n",
                        task.name(),
                        bar,
                        task.start(),
                        task.end(),
                        task.progress()
                    );
                });

            System.out.println();
            System.out.println(
                "Legend: | completed, . remaining, * milestone"
            );
        }

        void printStatusReport() {
            System.out.println("\nTask status");

            tasks.values().stream()
                .sorted(Comparator.comparing(Task::start))
                .forEach(task ->
                    System.out.printf(
                        "%s: %-15s %s%n",
                        task.id(),
                        task.status(),
                        task.name()
                    )
                );
        }
    }

    public static void main(String[] args) {
        Schedule schedule =
            new Schedule("Enterprise Procurement Automation");

        schedule.addTask(new Task(
            "REQ",
            "Requirements Analysis",
            LocalDate.of(2026, 10, 12),
            LocalDate.of(2026, 10, 16),
            List.of(),
            "Business Analysis",
            100,
            false
        ));

        schedule.addTask(new Task(
            "ARCH",
            "Architecture",
            LocalDate.of(2026, 10, 19),
            LocalDate.of(2026, 10, 23),
            List.of("REQ"),
            "Architecture",
            80,
            false
        ));

        schedule.addTask(new Task(
            "DB",
            "Database Implementation",
            LocalDate.of(2026, 10, 26),
            LocalDate.of(2026, 10, 30),
            List.of("ARCH"),
            "Backend",
            50,
            false
        ));

        schedule.addTask(new Task(
            "APP",
            "Application Development",
            LocalDate.of(2026, 10, 26),
            LocalDate.of(2026, 11, 13),
            List.of("ARCH"),
            "Backend",
            35,
            false
        ));

        schedule.addTask(new Task(
            "TEST",
            "Integration Testing",
            LocalDate.of(2026, 11, 16),
            LocalDate.of(2026, 11, 20),
            List.of("DB", "APP"),
            "QA",
            0,
            false
        ));

        schedule.addTask(new Task(
            "LIVE",
            "Production Release",
            LocalDate.of(2026, 11, 23),
            LocalDate.of(2026, 11, 23),
            List.of("TEST"),
            "Release Management",
            0,
            true
        ));

        try {
            schedule.validate();
            schedule.render();
            schedule.printStatusReport();

            System.out.println("\nCritical path");
            System.out.println(
                String.join(" -> ", schedule.criticalPath())
            );

            System.out.println("\nResource conflicts");
            Map<String, List<String>> conflicts =
                schedule.resourceConflicts();

            if (conflicts.isEmpty()) {
                System.out.println("No resource conflicts detected.");
            } else {
                conflicts.forEach((resource, items) -> {
                    System.out.println(resource + ":");
                    items.forEach(item ->
                        System.out.println("  " + item)
                    );
                });
            }
        } catch (RuntimeException error) {
            System.err.println(
                "Schedule validation failed: " + error.getMessage()
            );
        }
    }
}
