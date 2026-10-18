import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

/**
 * Enterprise resource allocation for a software delivery organization.
 *
 * The model separates resource eligibility, task dependencies, planning,
 * and validation so that allocation policy can be tested independently
 * from reporting.
 *
 * Compile: javac ResourceAllocation.java
 * Run:     java ResourceAllocation
 */
public class ResourceAllocation {

    enum ResourceType {
        COMPUTE, DATABASE, OPERATIONS
    }

    record Resource(
            String id,
            ResourceType type,
            double capacity,
            double hourlyCost,
            Set<String> tags) {

        Resource {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("Resource ID is required.");
            }
            if (type == null || capacity <= 0 || hourlyCost < 0) {
                throw new IllegalArgumentException("Invalid resource values.");
            }
            tags = Set.copyOf(tags);
        }

        boolean supports(Task task) {
            return type == task.type()
                    && capacity >= task.demand()
                    && tags.containsAll(task.requiredTags());
        }
    }

    record Task(
            String id,
            String description,
            ResourceType type,
            double demand,
            double duration,
            int priority,
            List<String> dependencies,
            Set<String> requiredTags,
            double deadline) {

        Task {
            if (id == null || id.isBlank() ||
                    description == null || description.isBlank()) {
                throw new IllegalArgumentException(
                        "Task identity and description are required.");
            }
            if (type == null || demand <= 0 || duration <= 0 || priority < 0) {
                throw new IllegalArgumentException("Invalid task values.");
            }
            if (dependencies.contains(id)) {
                throw new IllegalArgumentException(
                        "A task cannot depend on itself.");
            }
            dependencies = List.copyOf(new TreeSet<>(dependencies));
            requiredTags = Set.copyOf(requiredTags);
        }
    }

    record Assignment(
            String taskId,
            String resourceId,
            double demand,
            double start,
            double finish) {
    }

    record Rejection(String taskId, String reason) {
    }

    static final class Plan {
        private final List<Assignment> assignments;
        private final List<Rejection> rejections;

        Plan(List<Assignment> assignments, List<Rejection> rejections) {
            this.assignments = List.copyOf(assignments);
            this.rejections = List.copyOf(rejections);
        }

        List<Assignment> assignments() {
            return assignments;
        }

        List<Rejection> rejections() {
            return rejections;
        }
    }

    static final class AllocationService {
        private final Map<String, Resource> resources = new LinkedHashMap<>();
        private final Map<String, Task> tasks = new LinkedHashMap<>();

        AllocationService(List<Resource> resourceList, List<Task> taskList) {
            for (Resource resource : resourceList) {
                if (resources.putIfAbsent(resource.id(), resource) != null) {
                    throw new IllegalArgumentException(
                            "Duplicate resource: " + resource.id());
                }
            }
            for (Task task : taskList) {
                if (tasks.putIfAbsent(task.id(), task) != null) {
                    throw new IllegalArgumentException(
                            "Duplicate task: " + task.id());
                }
            }
            validateDependencies();
        }

        private void validateDependencies() {
            for (Task task : tasks.values()) {
                for (String dependency : task.dependencies()) {
                    if (!tasks.containsKey(dependency)) {
                        throw new IllegalArgumentException(
                                "Unknown dependency " + dependency
                                        + " for " + task.id());
                    }
                }
            }

            Set<String> visiting = new HashSet<>();
            Set<String> visited = new HashSet<>();
            for (String taskId : tasks.keySet()) {
                visit(taskId, visiting, visited);
            }
        }

        private void visit(
                String taskId,
                Set<String> visiting,
                Set<String> visited) {

            if (visiting.contains(taskId)) {
                throw new IllegalArgumentException(
                        "Dependency cycle involving " + taskId);
            }
            if (visited.contains(taskId)) {
                return;
            }

            visiting.add(taskId);
            for (String dependency : tasks.get(taskId).dependencies()) {
                visit(dependency, visiting, visited);
            }
            visiting.remove(taskId);
            visited.add(taskId);
        }

        Plan allocate() {
            Map<String, List<Assignment>> reservations = new HashMap<>();
            resources.keySet().forEach(id -> reservations.put(id, new ArrayList<>()));

            Map<String, Double> finishTimes = new HashMap<>();
            Set<String> pending = new HashSet<>(tasks.keySet());
            List<Assignment> assignments = new ArrayList<>();
            List<Rejection> rejections = new ArrayList<>();

            Comparator<Task> schedulingOrder =
                    Comparator.comparingInt(Task::priority).reversed()
                            .thenComparingDouble(Task::deadline)
                            .thenComparing(Task::id);

            while (!pending.isEmpty()) {
                List<Task> ready = pending.stream()
                        .map(tasks::get)
                        .filter(task -> task.dependencies().stream().allMatch(
                                dependency -> finishTimes.containsKey(dependency)
                                        || rejections.stream().anyMatch(
                                                rejection -> rejection.taskId()
                                                        .equals(dependency))))
                        .sorted(schedulingOrder)
                        .toList();

                if (ready.isEmpty()) {
                    for (String taskId : pending) {
                        rejections.add(new Rejection(
                                taskId, "Dependency resolution failed."));
                    }
                    break;
                }

                Task task = ready.get(0);
                pending.remove(task.id());

                String failedDependency = task.dependencies().stream()
                        .filter(dependency -> rejections.stream().anyMatch(
                                rejection -> rejection.taskId().equals(dependency)))
                        .findFirst()
                        .orElse(null);

                if (failedDependency != null) {
                    rejections.add(new Rejection(
                            task.id(),
                            "Dependency " + failedDependency + " was rejected."));
                    continue;
                }

                double dependencyFinish = task.dependencies().stream()
                        .mapToDouble(finishTimes::get)
                        .max()
                        .orElse(0.0);

                record Candidate(Resource resource, double start) {}

                List<Candidate> candidates = new ArrayList<>();

                for (Resource resource : resources.values()) {
                    if (!resource.supports(task)) {
                        continue;
                    }

                    double start = earliestStart(
                            reservations.get(resource.id()),
                            dependencyFinish,
                            task.duration());

                    if (start + task.duration() <= task.deadline()) {
                        candidates.add(new Candidate(resource, start));
                    }
                }

                candidates.sort(
                        Comparator.comparingDouble(Candidate::start)
                                .thenComparingDouble(
                                        candidate -> candidate.resource().hourlyCost())
                                .thenComparing(
                                        candidate -> candidate.resource().id()));

                if (candidates.isEmpty()) {
                    rejections.add(new Rejection(
                            task.id(),
                            "No compatible resource meets the deadline."));
                    continue;
                }

                Candidate chosen = candidates.get(0);
                Assignment assignment = new Assignment(
                        task.id(),
                        chosen.resource().id(),
                        task.demand(),
                        chosen.start(),
                        chosen.start() + task.duration());

                reservations.get(chosen.resource().id()).add(assignment);
                assignments.add(assignment);
                finishTimes.put(task.id(), assignment.finish());
            }

            return new Plan(assignments, rejections);
        }

        private double earliestStart(
                List<Assignment> existing,
                double requestedStart,
                double duration) {

            List<Assignment> sorted = existing.stream()
                    .sorted(Comparator.comparingDouble(Assignment::start))
                    .toList();

            double candidate = requestedStart;

            for (Assignment assignment : sorted) {
                if (candidate + duration <= assignment.start()) {
                    break;
                }
                if (candidate < assignment.finish()) {
                    candidate = assignment.finish();
                }
            }
            return candidate;
        }

        List<String> validate(Plan plan) {
            List<String> errors = new ArrayList<>();
            Map<String, List<Assignment>> byResource = new HashMap<>();
            Map<String, Assignment> byTask = new HashMap<>();

            for (Assignment assignment : plan.assignments()) {
                Resource resource = resources.get(assignment.resourceId());
                Task task = tasks.get(assignment.taskId());

                if (resource == null || task == null) {
                    errors.add("Unknown task or resource.");
                    continue;
                }
                if (!resource.supports(task)) {
                    errors.add("Incompatible assignment: " + task.id());
                }
                if (Math.abs(assignment.demand() - task.demand()) > 1e-9) {
                    errors.add("Demand mismatch: " + task.id());
                }
                if (assignment.finish() <= assignment.start()) {
                    errors.add("Invalid interval: " + task.id());
                }
                if (byTask.putIfAbsent(task.id(), assignment) != null) {
                    errors.add("Task assigned more than once: " + task.id());
                }
                byResource.computeIfAbsent(
                        resource.id(), ignored -> new ArrayList<>()).add(assignment);
            }

            for (Map.Entry<String, List<Assignment>> entry : byResource.entrySet()) {
                List<Assignment> scheduled = entry.getValue().stream()
                        .sorted(Comparator.comparingDouble(Assignment::start))
                        .toList();

                for (int i = 1; i < scheduled.size(); i++) {
                    if (scheduled.get(i).start()
                            < scheduled.get(i - 1).finish()) {
                        errors.add("Reservation overlap on " + entry.getKey());
                    }
                }
            }

            for (Assignment assignment : plan.assignments()) {
                Task task = tasks.get(assignment.taskId());
                for (String dependency : task.dependencies()) {
                    Assignment prerequisite = byTask.get(dependency);
                    if (prerequisite == null) {
                        errors.add("Missing prerequisite " + dependency
                                + " for " + task.id());
                    } else if (assignment.start() < prerequisite.finish()) {
                        errors.add("Dependency timing violation: " + task.id());
                    }
                }
            }

            return errors;
        }

        double estimateCost(Plan plan) {
            return plan.assignments().stream()
                    .mapToDouble(assignment -> {
                        Resource resource = resources.get(assignment.resourceId());
                        return (assignment.finish() - assignment.start())
                                * resource.hourlyCost();
                    })
                    .sum();
        }
    }

    public static void main(String[] args) {
        List<Resource> resources = List.of(
                new Resource("GPU-01", ResourceType.COMPUTE,
                        16, 18, Set.of("cuda", "linux")),
                new Resource("CPU-01", ResourceType.COMPUTE,
                        8, 6, Set.of("linux")),
                new Resource("DB-01", ResourceType.DATABASE,
                        12, 14, Set.of("postgresql", "backup")),
                new Resource("OPS-01", ResourceType.OPERATIONS,
                        4, 10, Set.of("production"))
        );

        List<Task> tasks = List.of(
                new Task("PREP", "Prepare data", ResourceType.COMPUTE,
                        6, 2, 8, List.of(), Set.of("linux"), 10),
                new Task("TRAIN", "Train forecasting model", ResourceType.COMPUTE,
                        14, 4, 10, List.of("PREP"), Set.of("cuda"), 9),
                new Task("DB-MIGRATION", "Migrate analytics database",
                        ResourceType.DATABASE, 8, 3, 7, List.of(),
                        Set.of("postgresql", "backup"), 8),
                new Task("VERIFY", "Verify predictions", ResourceType.COMPUTE,
                        4, 2, 6, List.of("TRAIN"), Set.of("linux"), 12),
                new Task("DEPLOY", "Deploy service", ResourceType.OPERATIONS,
                        3, 2, 10, List.of("DB-MIGRATION", "VERIFY"),
                        Set.of("production"), 16),
                new Task("OVERSIZED", "Large simulation", ResourceType.COMPUTE,
                        32, 5, 2, List.of(), Set.of("linux"), 100)
        );

        try {
            AllocationService service = new AllocationService(resources, tasks);
            Plan plan = service.allocate();

            System.out.printf("%-16s %-14s %8s %8s %8s%n",
                    "Task", "Resource", "Start", "Finish", "Demand");

            for (Assignment assignment : plan.assignments()) {
                System.out.printf("%-16s %-14s %8.1f %8.1f %8.1f%n",
                        assignment.taskId(),
                        assignment.resourceId(),
                        assignment.start(),
                        assignment.finish(),
                        assignment.demand());
            }

            System.out.println("\nRejected work:");
            for (Rejection rejection : plan.rejections()) {
                System.out.println(
                        rejection.taskId() + ": " + rejection.reason());
            }

            System.out.printf("%nEstimated cost: %.2f%n",
                    service.estimateCost(plan));

            List<String> errors = service.validate(plan);
            if (errors.isEmpty()) {
                System.out.println("Validation: PASSED");
            } else {
                errors.forEach(System.err::println);
                System.exitCode = 1;
            }
        } catch (IllegalArgumentException exception) {
            System.err.println("Allocation policy error: " + exception.getMessage());
            System.exitCode = 1;
        }
    }
}
