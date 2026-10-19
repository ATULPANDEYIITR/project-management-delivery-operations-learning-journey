import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public class ResourceAvailabilityManager {

    enum ResourceType {
        COMPUTE,
        MEMORY,
        STORAGE,
        DATABASE_CONNECTIONS,
        API_QUOTA
    }

    enum Priority {
        LOW(10),
        NORMAL(20),
        HIGH(30),
        CRITICAL(40);

        private final int weight;

        Priority(int weight) {
            this.weight = weight;
        }

        public int weight() {
            return weight;
        }
    }

    record ResourceRequirement(ResourceType type, long amount) {
        ResourceRequirement {
            Objects.requireNonNull(type, "Resource type is required");
            if (amount <= 0) {
                throw new IllegalArgumentException(
                    "Resource amount must be positive"
                );
            }
        }
    }

    record AllocationResult(boolean accepted, String reason) {}

    static final class ResourcePool {
        private final String name;
        private final ResourceType type;
        private final long capacity;
        private long available;
        private final Map<String, Long> allocations = new HashMap<>();

        ResourcePool(String name, ResourceType type, long capacity) {
            if (capacity <= 0) {
                throw new IllegalArgumentException(
                    "Capacity must be positive"
                );
            }

            this.name = Objects.requireNonNull(name);
            this.type = Objects.requireNonNull(type);
            this.capacity = capacity;
            this.available = capacity;
        }

        boolean canAllocate(long amount) {
            return amount > 0 && amount <= available;
        }

        void allocate(String owner, long amount) {
            if (!canAllocate(amount)) {
                throw new IllegalStateException(
                    "Insufficient capacity in " + name
                );
            }

            available -= amount;
            allocations.merge(owner, amount, Long::sum);
        }

        long release(String owner) {
            Long amount = allocations.remove(owner);

            if (amount == null) {
                return 0;
            }

            available += amount;
            return amount;
        }

        long capacity() {
            return capacity;
        }

        long available() {
            return available;
        }

        double utilization() {
            return (double) (capacity - available) / capacity;
        }

        ResourceType type() {
            return type;
        }

        String name() {
            return name;
        }
    }

    record Workload(
        String id,
        String owner,
        Priority priority,
        List<ResourceRequirement> requirements,
        long estimatedDurationMillis
    ) {
        Workload {
            Objects.requireNonNull(id);
            Objects.requireNonNull(owner);
            Objects.requireNonNull(priority);
            Objects.requireNonNull(requirements);

            if (id.isBlank() || owner.isBlank()) {
                throw new IllegalArgumentException(
                    "Workload identity cannot be blank"
                );
            }

            if (estimatedDurationMillis <= 0) {
                throw new IllegalArgumentException(
                    "Estimated duration must be positive"
                );

            requirements = List.copyOf(requirements);
        }
    }

    static final class ResourceService {
        private final EnumMap<ResourceType, ResourcePool> pools =
            new EnumMap<>(ResourceType.class);

        void register(
            ResourceType type,
            String name,
            long capacity
        ) {
            if (pools.containsKey(type)) {
                throw new IllegalArgumentException(
                    "Pool already registered for " + type
                );
            }

            pools.put(type, new ResourcePool(name, type, capacity));
        }

        /*
         * Requirements are aggregated before allocation. This matters when a
         * workload requests the same resource type through several components.
         * All availability checks happen before state mutation, giving the
         * operation atomic admission semantics.
         */
        synchronized AllocationResult allocate(
            String owner,
            List<ResourceRequirement> requirements
        ) {
            if (owner == null || owner.isBlank()) {
                throw new IllegalArgumentException(
                    "Owner is required"
                );
            }

            EnumMap<ResourceType, Long> totals =
                new EnumMap<>(ResourceType.class);

            for (ResourceRequirement requirement : requirements) {
                totals.merge(
                    requirement.type(),
                    requirement.amount(),
                    Long::sum
                );
            }

            for (var entry : totals.entrySet()) {
                ResourcePool pool = pools.get(entry.getKey());

                if (pool == null) {
                    return new AllocationResult(
                        false,
                        "Resource pool is not configured: "
                            + entry.getKey()
                    );
                }

                if (!pool.canAllocate(entry.getValue())) {
                    return new AllocationResult(
                        false,
                        "Insufficient " + entry.getKey()
                    );
                }
            }

            for (var entry : totals.entrySet()) {
                pools.get(entry.getKey())
                    .allocate(owner, entry.getValue());
            }

            return new AllocationResult(true, "Capacity reserved");
        }

        synchronized long release(String owner) {
            return pools.values()
                .stream()
                .mapToLong(pool -> pool.release(owner))
                .sum();
        }

        synchronized void printCapacity() {
            System.out.printf(
                "%-25s %-15s %-15s %-12s%n",
                "Pool",
                "Capacity",
                "Available",
                "Utilization"
            );

            pools.values().forEach(pool ->
                System.out.printf(
                    "%-25s %-15d %-15d %.1f%%%n",
                    pool.name(),
                    pool.capacity(),
                    pool.available(),
                    pool.utilization() * 100
                )
            );
        }
    }

    static final class AdmissionPolicy {
        private final ResourceService resourceService;

        AdmissionPolicy(ResourceService resourceService) {
            this.resourceService = resourceService;
        }

        List<Workload> admit(List<Workload> workloads) {
            List<Workload> ordered = new ArrayList<>(workloads);

            ordered.sort(
                Comparator.comparing(
                    Workload::priority,
                    Comparator.comparingInt(Priority::weight)
                ).reversed()
            );

            List<Workload> admitted = new ArrayList<>();

            for (Workload workload : ordered) {
                AllocationResult result =
                    resourceService.allocate(
                        workload.owner(),
                        workload.requirements()
                    );

                if (result.accepted()) {
                    admitted.add(workload);
                    System.out.println(
                        "Admitted " + workload.id()
                    );
                } else {
                    System.out.println(
                        "Deferred " + workload.id()
                            + ": " + result.reason()
                    );
                }
            }

            return admitted;
        }
    }

    private static ResourceService createProductionPools() {
        ResourceService service = new ResourceService();

        service.register(
            ResourceType.COMPUTE,
            "Application Compute",
            32
        );
        service.register(
            ResourceType.MEMORY,
            "Application Memory",
            128
        );
        service.register(
            ResourceType.STORAGE,
            "Object Storage",
            5000
        );
        service.register(
            ResourceType.DATABASE_CONNECTIONS,
            "PostgreSQL Connections",
            40
        );
        service.register(
            ResourceType.API_QUOTA,
            "External API Quota",
            10000
        );

        return service;
    }

    private static void runEnterpriseScenario() {
        ResourceService service = createProductionPools();
        AdmissionPolicy policy = new AdmissionPolicy(service);

        List<Workload> workloads = List.of(
            new Workload(
                "customer-search",
                "customer-platform",
                Priority.HIGH,
                List.of(
                    new ResourceRequirement(
                        ResourceType.COMPUTE,
                        8
                    ),
                    new ResourceRequirement(
                        ResourceType.MEMORY,
                        32
                    ),
                    new ResourceRequirement(
                        ResourceType.DATABASE_CONNECTIONS,
                        10
                    )
                ),
                500
            ),
            new Workload(
                "monthly-archive",
                "records-team",
                Priority.LOW,
                List.of(
                    new ResourceRequirement(
                        ResourceType.COMPUTE,
                        12
                    ),
                    new ResourceRequirement(
                        ResourceType.STORAGE,
                        2000
                    )
                ),
                5000
            ),
            new Workload(
                "payment-recovery",
                "payments",
                Priority.CRITICAL,
                List.of(
                    new ResourceRequirement(
                        ResourceType.COMPUTE,
                        10
                    ),
                    new ResourceRequirement(
                        ResourceType.MEMORY,
                        48
                    ),
                    new ResourceRequirement(
                        ResourceType.DATABASE_CONNECTIONS,
                        12
                    )
                ),
                300
            )
        );

        System.out.println("Capacity before admission:");
        service.printCapacity();

        System.out.println("\nAdmission decisions:");
        List<Workload> admitted = policy.admit(workloads);

        System.out.println(
            "\nRunning workloads: " + admitted.size()
        );

        System.out.println("\nCapacity while workloads run:");
        service.printCapacity();

        service.release("payments");

        System.out.println("\nCapacity after payment recovery:");
        service.printCapacity();
    }

    private static void demonstrateInvalidRequest() {
        try {
            new ResourceRequirement(
                ResourceType.COMPUTE,
                0
            );
        } catch (IllegalArgumentException exception) {
            System.out.println(
                "\nInvalid resource request rejected: "
                    + exception.getMessage()
            );
        }
    }

    public static void main(String[] args) {
        runEnterpriseScenario();
        demonstrateInvalidRequest();
    }
}
