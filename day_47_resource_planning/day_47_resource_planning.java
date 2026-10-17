import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class ResourcePlanningEnterprise {

    enum ResourceType {
        PERSON,
        EQUIPMENT,
        SOFTWARE
    }

    enum SkillLevel {
        JUNIOR(1),
        MID(2),
        SENIOR(3),
        EXPERT(4);

        private final int rank;

        SkillLevel(int rank) {
            this.rank = rank;
        }

        public int rank() {
            return rank;
        }
    }

    enum TaskState {
        PLANNED,
        ACTIVE,
        BLOCKED,
        COMPLETED
    }

    record Resource(
        String id,
        String name,
        ResourceType type,
        Set<String> skills,
        SkillLevel skillLevel,
        double weeklyCapacity,
        double hourlyCost
    ) {
        Resource {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("Resource ID is required.");
            }
            if (weeklyCapacity <= 0 || hourlyCost < 0) {
                throw new IllegalArgumentException(
                    "Resource capacity and cost are invalid."
                );
            }

            skills = Set.copyOf(skills);
        }

        boolean canPerform(Task task) {
            return skillLevel.rank() >= task.minimumSkillLevel().rank()
                && skills.containsAll(task.requiredSkills());
        }
    }

    record Task(
        String id,
        String name,
        Set<String> requiredSkills,
        SkillLevel minimumSkillLevel,
        double estimatedHours,
        int priority,
        TaskState state
    ) {
        Task {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("Task ID is required.");
            }
            if (estimatedHours <= 0) {
                throw new IllegalArgumentException(
                    "Estimated effort must be positive."
                );
            }

            requiredSkills = Set.copyOf(requiredSkills);
        }

        Task activate() {
            if (state != TaskState.PLANNED) {
                throw new IllegalStateException(
                    "Only planned tasks can become active."
                );
            }

            return new Task(
                id,
                name,
                requiredSkills,
                minimumSkillLevel,
                estimatedHours,
                priority,
                TaskState.ACTIVE
            );
        }

        Task block() {
            if (state == TaskState.COMPLETED) {
                throw new IllegalStateException(
                    "Completed tasks cannot be blocked."
                );
            }

            return new Task(
                id,
                name,
                requiredSkills,
                minimumSkillLevel,
                estimatedHours,
                priority,
                TaskState.BLOCKED
            );
        }
    }

    record Allocation(
        String resourceId,
        String taskId,
        double hours
    ) {
        Allocation {
            if (hours <= 0) {
                throw new IllegalArgumentException(
                    "Allocation hours must be positive."
                );
            }
        }
    }

    static final class ResourceAllocationException
        extends RuntimeException {

        ResourceAllocationException(String message) {
            super(message);
        }
    }

    static final class ResourcePlanService {
        private final Map<String, Resource> resources = new HashMap<>();
        private final Map<String, Task> tasks = new HashMap<>();
        private final List<Allocation> allocations = new ArrayList<>();
        private final double projectBudget;

        ResourcePlanService(double projectBudget) {
            if (projectBudget <= 0) {
                throw new IllegalArgumentException(
                    "Project budget must be positive."
                );
            }

            this.projectBudget = projectBudget;
        }

        void registerResource(Resource resource) {
            if (resources.putIfAbsent(resource.id(), resource) != null) {
                throw new IllegalArgumentException(
                    "Resource already registered: " + resource.id()
                );
            }
        }

        void registerTask(Task task) {
            if (tasks.putIfAbsent(task.id(), task) != null) {
                throw new IllegalArgumentException(
                    "Task already registered: " + task.id()
                );
            }
        }

        List<Resource> findEligiblePeople(String taskId) {
            Task task = requireTask(taskId);

            return resources.values()
                .stream()
                .filter(resource ->
                    resource.type() == ResourceType.PERSON
                    && resource.canPerform(task)
                )
                .sorted(
                    java.util.Comparator
                        .comparingDouble(Resource::hourlyCost)
                )
                .toList();
        }

        void allocate(String taskId, String resourceId, double hours) {
            Task task = requireTask(taskId);
            Resource resource = requireResource(resourceId);

            if (resource.type() != ResourceType.PERSON) {
                throw new ResourceAllocationException(
                    "This allocation workflow requires a person resource."
                );
            }

            if (!resource.canPerform(task)) {
                throw new ResourceAllocationException(
                    resource.name()
                    + " does not satisfy the task qualification policy."
                );
            }

            double existingHours = allocatedHours(resourceId);

            if (existingHours + hours > resource.weeklyCapacity()) {
                throw new ResourceAllocationException(
                    "Allocation exceeds available capacity for "
                    + resource.name()
                );
            }

            double taskRemaining =
                task.estimatedHours() - allocatedTaskHours(taskId);

            if (hours > taskRemaining) {
                throw new ResourceAllocationException(
                    "Allocation exceeds remaining task effort."
                );
            }

            double projectedCost =
                projectedCost(resource, hours);

            if (currentCost() + projectedCost > projectBudget) {
                throw new ResourceAllocationException(
                    "Allocation would exceed the project budget."
                );
            }

            allocations.add(
                new Allocation(resourceId, taskId, hours)
            );
        }

        double allocatedHours(String resourceId) {
            return allocations.stream()
                .filter(a -> a.resourceId().equals(resourceId))
                .mapToDouble(Allocation::hours)
                .sum();
        }

        double allocatedTaskHours(String taskId) {
            return allocations.stream()
                .filter(a -> a.taskId().equals(taskId))
                .mapToDouble(Allocation::hours)
                .sum();
        }

        double projectedCost(Resource resource, double hours) {
            return resource.hourlyCost() * hours;
        }

        double currentCost() {
            return allocations.stream()
                .mapToDouble(allocation -> {
                    Resource resource =
                        resources.get(allocation.resourceId());

                    return resource.hourlyCost()
                        * allocation.hours();
                })
                .sum();
        }

        double remainingBudget() {
            return projectBudget - currentCost();
        }

        void printResourceCapacity() {
            System.out.println("\nResource capacity");

            resources.values().stream()
                .filter(r -> r.type() == ResourceType.PERSON)
                .forEach(resource -> {
                    double used = allocatedHours(resource.id());
                    double percentage =
                        used / resource.weeklyCapacity() * 100.0;

                    System.out.printf(
                        "%-18s %6.1f / %6.1f hours (%6.2f%%)%n",
                        resource.name(),
                        used,
                        resource.weeklyCapacity(),
                        percentage
                    );
                });
        }

        private Task requireTask(String id) {
            Task task = tasks.get(id);

            if (task == null) {
                throw new IllegalArgumentException(
                    "Unknown task: " + id
                );
            }

            return task;
        }

        private Resource requireResource(String id) {
            Resource resource = resources.get(id);

            if (resource == null) {
                throw new IllegalArgumentException(
                    "Unknown resource: " + id
                );
            }

            return resource;
        }
    }

    public static void main(String[] args) {
        ResourcePlanService service =
            new ResourcePlanService(120_000.00);

        service.registerResource(
            new Resource(
                "P-001",
                "Asha Rao",
                ResourceType.PERSON,
                Set.of(
                    "backend",
                    "api",
                    "security",
                    "postgresql"
                ),
                SkillLevel.SENIOR,
                40,
                75
            )
        );

        service.registerResource(
            new Resource(
                "P-002",
                "Vikram Singh",
                ResourceType.PERSON,
                Set.of(
                    "frontend",
                    "javascript",
                    "accessibility"
                ),
                SkillLevel.SENIOR,
                40,
                68
            )
        );

        service.registerResource(
            new Resource(
                "P-003",
                "Meera Shah",
                ResourceType.PERSON,
                Set.of(
                    "security",
                    "testing",
                    "cloud"
                ),
                SkillLevel.EXPERT,
                32,
                92
            )
        );

        service.registerResource(
            new Resource(
                "EQ-001",
                "Performance Test Cluster",
                ResourceType.EQUIPMENT,
                Set.of(),
                SkillLevel.EXPERT,
                80,
                25
            )
        );

        service.registerTask(
            new Task(
                "T-001",
                "Secure service implementation",
                Set.of("backend", "api", "security"),
                SkillLevel.SENIOR,
                72,
                1,
                TaskState.PLANNED
            )
        );

        service.registerTask(
            new Task(
                "T-002",
                "Accessible public portal",
                Set.of("frontend", "javascript", "accessibility"),
                SkillLevel.SENIOR,
                64,
                2,
                TaskState.PLANNED
            )
        );

        service.registerTask(
            new Task(
                "T-003",
                "Security validation",
                Set.of("security", "testing"),
                SkillLevel.EXPERT,
                40,
                1,
                TaskState.PLANNED
            )
        );

        System.out.println("Eligible resources for security validation:");

        service.findEligiblePeople("T-003")
            .forEach(resource ->
                System.out.printf(
                    "  %s, %s, $%.2f/hour%n",
                    resource.name(),
                    resource.skillLevel(),
                    resource.hourlyCost()
                )
            );

        service.allocate("T-001", "P-001", 72);
        service.allocate("T-002", "P-002", 64);
        service.allocate("T-003", "P-003", 40);

        try {
            /*
             * The exception is raised before the invalid allocation is
             * persisted. This keeps domain rules inside the service boundary
             * instead of requiring callers to duplicate capacity checks.
             */
            service.allocate("T-003", "P-001", 20);
        } catch (ResourceAllocationException exception) {
            System.out.println(
                "\nRejected allocation: "
                + exception.getMessage()
            );
        }

        service.printResourceCapacity();

        System.out.printf(
            "%nPlanned cost: $%,.2f%n",
            service.currentCost()
        );

        System.out.printf(
            "Remaining budget: $%,.2f%n",
            service.remainingBudget()
        );

        /*
         * Java records provide immutable domain values for resources,
         * tasks, and allocations. The service owns mutable workflow state,
         * creating a clear separation between domain data and orchestration.
         */
        Task activeTask =
            new Task(
                "T-004",
                "Operational monitoring",
                Set.of("cloud"),
                SkillLevel.MID,
                24,
                3,
                TaskState.PLANNED
            );

        service.registerTask(activeTask);

        Task activated = activeTask.activate();

        System.out.println(
            "\nState transition: "
            + activeTask.state()
            + " -> "
            + activated.state()
        );
    }
}
