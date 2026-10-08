import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/*
 * Critical Path Method: Enterprise Release Governance
 *
 * Java 17 implementation of a project scheduling domain.
 *
 * The model separates:
 *   - Activity: immutable project work definition
 *   - ScheduleEntry: calculated timing state
 *   - ProjectSchedule: dependency graph and CPM engine
 *   - SchedulePolicy: business rules for classifying activities
 *
 * The scenario represents an enterprise platform release where activities
 * have explicit dependencies and release readiness depends on multiple
 * parallel workstreams.
 */

public class CriticalPathDemo {

    private static final double EPSILON = 1e-9;

    public record Activity(
        String id,
        String name,
        double duration,
        List<String> predecessors
    ) {
        public Activity {
            Objects.requireNonNull(id, "id");
            Objects.requireNonNull(name, "name");
            Objects.requireNonNull(predecessors, "predecessors");

            if (id.isBlank()) {
                throw new IllegalArgumentException(
                    "Activity ID cannot be blank."
                );
            }

            if (name.isBlank()) {
                throw new IllegalArgumentException(
                    "Activity name cannot be blank."
                );
            }

            if (!Double.isFinite(duration) || duration < 0) {
                throw new IllegalArgumentException(
                    "Activity duration must be finite and non-negative."
                );
            }

            predecessors = List.copyOf(predecessors);

            if (new HashSet<>(predecessors).size()
                != predecessors.size()) {
                throw new IllegalArgumentException(
                    "Duplicate predecessors are not allowed for " + id
                );
            }
        }
    }

    public static final class ScheduleEntry {
        private final Activity activity;
        private final double earliestStart;
        private final double earliestFinish;
        private final double latestStart;
        private final double latestFinish;
        private final double totalFloat;

        public ScheduleEntry(
            Activity activity,
            double earliestStart,
            double earliestFinish,
            double latestStart,
            double latestFinish,
            double totalFloat
        ) {
            this.activity = activity;
            this.earliestStart = earliestStart;
            this.earliestFinish = earliestFinish;
            this.latestStart = latestStart;
            this.latestFinish = latestFinish;
            this.totalFloat = totalFloat;
        }

        public Activity activity() {
            return activity;
        }

        public double earliestStart() {
            return earliestStart;
        }

        public double earliestFinish() {
            return earliestFinish;
        }

        public double latestStart() {
            return latestStart;
        }

        public double latestFinish() {
            return latestFinish;
        }

        public double totalFloat() {
            return totalFloat;
        }

        public boolean isCritical() {
            return Math.abs(totalFloat) <= EPSILON;
        }
    }

    /*
     * This policy is deliberately separate from the scheduling calculation.
     * CPM calculates timing values; the policy decides how those values are
     * interpreted by the enterprise scheduling process.
     */
    public interface SchedulePolicy {
        boolean isCritical(ScheduleEntry entry);

        String classification(ScheduleEntry entry);
    }

    public static final class ZeroFloatPolicy
        implements SchedulePolicy {

        @Override
        public boolean isCritical(ScheduleEntry entry) {
            return Math.abs(entry.totalFloat()) <= EPSILON;
        }

        @Override
        public String classification(ScheduleEntry entry) {
            if (isCritical(entry)) {
                return "CRITICAL";
            }

            if (entry.totalFloat() <= 2.0) {
                return "LOW FLOAT";
            }

            return "NON-CRITICAL";
        }
    }

    public static final class ProjectSchedule {
        private final Map<String, Activity> activities;
        private final Map<String, List<String>> successors;
        private final List<String> topologicalOrder;
        private Map<String, ScheduleEntry> schedule =
            Collections.emptyMap();

        public ProjectSchedule(List<Activity> activityList) {
            Objects.requireNonNull(activityList);

            Map<String, Activity> mutableActivities =
                new HashMap<>();

            for (Activity activity : activityList) {
                if (mutableActivities.put(
                    activity.id(),
                    activity
                ) != null) {
                    throw new IllegalArgumentException(
                        "Duplicate activity ID: " + activity.id()
                    );
                }
            }

            this.activities =
                Collections.unmodifiableMap(mutableActivities);

            this.successors =
                buildSuccessors(this.activities);

            validateDependencies(
                this.activities,
                this.successors
            );

            this.topologicalOrder =
                Collections.unmodifiableList(
                    topologicalSort(
                        this.activities,
                        this.successors
                    )
                );
        }

        private static Map<String, List<String>> buildSuccessors(
            Map<String, Activity> activities
        ) {
            Map<String, List<String>> result =
                new HashMap<>();

            for (String id : activities.keySet()) {
                result.put(id, new ArrayList<>());
            }

            for (Activity activity : activities.values()) {
                for (String predecessor :
                    activity.predecessors()) {

                    result.get(predecessor)
                        .add(activity.id());
                }
            }

            return result;
        }

        private static void validateDependencies(
            Map<String, Activity> activities,
            Map<String, List<String>> successors
        ) {
            for (Activity activity : activities.values()) {
                for (String predecessor :
                    activity.predecessors()) {

                    if (!activities.containsKey(predecessor)) {
                        throw new IllegalArgumentException(
                            "Unknown predecessor " +
                            predecessor +
                            " for " +
                            activity.id()
                        );
                    }
                }
            }
        }

        private static List<String> topologicalSort(
            Map<String, Activity> activities,
            Map<String, List<String>> successors
        ) {
            Map<String, Integer> indegree =
                new HashMap<>();

            for (Activity activity : activities.values()) {
                indegree.put(
                    activity.id(),
                    activity.predecessors().size()
                );
            }

            Deque<String> queue = new ArrayDeque<>();

            for (Map.Entry<String, Integer> entry :
                indegree.entrySet()) {

                if (entry.getValue() == 0) {
                    queue.add(entry.getKey());
                }
            }

            List<String> result = new ArrayList<>();

            while (!queue.isEmpty()) {
                String current = queue.removeFirst();
                result.add(current);

                for (String successor :
                    successors.get(current)) {

                    int remaining =
                        indegree.get(successor) - 1;

                    indegree.put(successor, remaining);

                    if (remaining == 0) {
                        queue.addLast(successor);
                    }
                }
            }

            if (result.size() != activities.size()) {
                throw new IllegalArgumentException(
                    "Activity dependency graph contains a cycle."
                );
            }

            return result;
        }

        public void calculate() {
            Map<String, ScheduleEntry> forward =
                new HashMap<>();

            /*
             * Forward pass.
             *
             * Multiple predecessors create a synchronization point.
             * The activity starts only after the slowest predecessor
             * has finished.
             */
            for (String id : topologicalOrder) {
                Activity activity = activities.get(id);

                double earliestStart = 0.0;

                for (String predecessor :
                    activity.predecessors()) {

                    earliestStart = Math.max(
                        earliestStart,
                        forward.get(predecessor)
                            .earliestFinish()
                    );
                }

                double earliestFinish =
                    earliestStart + activity.duration();

                forward.put(
                    id,
                    new ScheduleEntry(
                        activity,
                        earliestStart,
                        earliestFinish,
                        0.0,
                        0.0,
                        0.0
                    )
                );
            }

            double projectDuration =
                forward.values()
                    .stream()
                    .mapToDouble(
                        ScheduleEntry::earliestFinish
                    )
                    .max()
                    .orElse(0.0);

            Map<String, ScheduleEntry> backward =
                new HashMap<>(forward);

            /*
             * Backward pass.
             *
             * A terminal activity is allowed to finish at project
             * completion. Other activities must finish before the
             * earliest latest-start requirement of their successors.
             */
            List<String> reverseOrder =
                new ArrayList<>(topologicalOrder);

            Collections.reverse(reverseOrder);

            for (String id : reverseOrder) {
                ScheduleEntry current = forward.get(id);

                double latestFinish =
                    successors.get(id).isEmpty()
                        ? projectDuration
                        : Double.POSITIVE_INFINITY;

                for (String successor :
                    successors.get(id)) {

                    latestFinish = Math.min(
                        latestFinish,
                        backward.get(successor)
                            .latestStart()
                    );
                }

                double latestStart =
                    latestFinish -
                    current.activity().duration();

                double totalFloat =
                    Math.max(
                        0.0,
                        latestStart -
                        current.earliestStart()
                    );

                backward.put(
                    id,
                    new ScheduleEntry(
                        current.activity(),
                        current.earliestStart(),
                        current.earliestFinish(),
                        latestStart,
                        latestFinish,
                        totalFloat
                    )
                );
            }

            schedule =
                Collections.unmodifiableMap(backward);
        }

        public double projectDuration() {
            ensureCalculated();

            return schedule.values()
                .stream()
                .mapToDouble(
                    ScheduleEntry::earliestFinish
                )
                .max()
                .orElse(0.0);
        }

        public List<ScheduleEntry> entries() {
            ensureCalculated();

            return topologicalOrder.stream()
                .map(schedule::get)
                .toList();
        }

        public List<ScheduleEntry> criticalActivities(
            SchedulePolicy policy
        ) {
            return entries()
                .stream()
                .filter(policy::isCritical)
                .toList();
        }

        public List<List<String>> criticalPaths(
            SchedulePolicy policy
        ) {
            ensureCalculated();

            Set<String> criticalIds =
                new HashSet<>(
                    criticalActivities(policy)
                        .stream()
                        .map(
                            entry ->
                                entry.activity().id()
                        )
                        .toList()
                );

            List<String> starts =
                topologicalOrder.stream()
                    .filter(criticalIds::contains)
                    .filter(id ->
                        activities.get(id)
                            .predecessors()
                            .stream()
                            .noneMatch(
                                criticalIds::contains
                            )
                    )
                    .toList();

            List<List<String>> paths =
                new ArrayList<>();

            for (String start : starts) {
                findPaths(
                    start,
                    criticalIds,
                    new ArrayList<>(List.of(start)),
                    paths
                );
            }

            return paths;
        }

        private void findPaths(
            String current,
            Set<String> criticalIds,
            List<String> path,
            List<List<String>> paths
        ) {
            List<String> next =
                successors.get(current)
                    .stream()
                    .filter(criticalIds::contains)
                    .filter(successor -> {
                        double gap =
                            schedule.get(successor)
                                .earliestStart()
                            -
                            schedule.get(current)
                                .earliestFinish();

                        return Math.abs(gap) <= EPSILON;
                    })
                    .toList();

            if (next.isEmpty()) {
                paths.add(List.copyOf(path));
                return;
            }

            for (String successor : next) {
                List<String> extended =
                    new ArrayList<>(path);

                extended.add(successor);

                findPaths(
                    successor,
                    criticalIds,
                    extended,
                    paths
                );
            }
        }

        private void ensureCalculated() {
            if (schedule.isEmpty()) {
                throw new IllegalStateException(
                    "Schedule has not been calculated."
                );
            }
        }

        public double simulateDelay(
            String activityId,
            double delay
        ) {
            if (!activities.containsKey(activityId)) {
                throw new IllegalArgumentException(
                    "Unknown activity: " + activityId
                );
            }

            if (!Double.isFinite(delay) || delay < 0) {
                throw new IllegalArgumentException(
                    "Delay must be finite and non-negative."
                );
            }

            List<Activity> modified =
                activities.values()
                    .stream()
                    .map(activity -> {
                        if (!activity.id()
                            .equals(activityId)) {
                            return activity;
                        }

                        return new Activity(
                            activity.id(),
                            activity.name(),
                            activity.duration() + delay,
                            activity.predecessors()
                        );
                    })
                    .toList();

            ProjectSchedule simulation =
                new ProjectSchedule(modified);

            simulation.calculate();

            return simulation.projectDuration();
        }
    }

    private static List<Activity> createEnterpriseRelease() {
        return List.of(
            new Activity(
                "REQ",
                "Requirements baseline",
                3,
                List.of()
            ),
            new Activity(
                "ARCH",
                "Architecture approval",
                4,
                List.of("REQ")
            ),
            new Activity(
                "DATA",
                "Data platform setup",
                5,
                List.of("ARCH")
            ),
            new Activity(
                "API",
                "Service implementation",
                7,
                List.of("ARCH")
            ),
            new Activity(
                "UI",
                "User interface implementation",
                6,
                List.of("ARCH")
            ),
            new Activity(
                "INT",
                "Integration validation",
                3,
                List.of("DATA", "API", "UI")
            ),
            new Activity(
                "PERF",
                "Performance validation",
                4,
                List.of("INT")
            ),
            new Activity(
                "SEC",
                "Security validation",
                5,
                List.of("INT")
            ),
            new Activity(
                "OPS",
                "Operations readiness",
                2,
                List.of("ARCH")
            ),
            new Activity(
                "REL",
                "Production release",
                2,
                List.of("PERF", "SEC", "OPS")
            )
        );
    }

    private static void printSchedule(
        ProjectSchedule project,
        SchedulePolicy policy
    ) {
        System.out.println("\nENTERPRISE RELEASE SCHEDULE");
        System.out.println(
            "================================================================================"
        );

        System.out.printf(
            "%-8s %-31s %7s %7s %7s %7s %7s %9s %-14s%n",
            "ID",
            "Activity",
            "Dur",
            "ES",
            "EF",
            "LS",
            "LF",
            "Float",
            "Class"
        );

        System.out.println(
            "--------------------------------------------------------------------------------"
        );

        for (ScheduleEntry entry : project.entries()) {
            System.out.printf(
                "%-8s %-31s %7.1f %7.1f %7.1f %7.1f %7.1f %9.1f %-14s%n",
                entry.activity().id(),
                entry.activity().name(),
                entry.activity().duration(),
                entry.earliestStart(),
                entry.earliestFinish(),
                entry.latestStart(),
                entry.latestFinish(),
                entry.totalFloat(),
                policy.classification(entry)
            );
        }

        System.out.println(
            "--------------------------------------------------------------------------------"
        );

        System.out.printf(
            "Project duration: %.1f%n",
            project.projectDuration()
        );

        System.out.println("\nCritical path(s):");

        for (List<String> path :
            project.criticalPaths(policy)) {
            System.out.println(
                "  " + String.join(" -> ", path)
            );
        }
    }

    private static void demonstrateDelayAnalysis(
        ProjectSchedule project
    ) {
        System.out.println("\nDELAY ANALYSIS");

        double baseline =
            project.projectDuration();

        for (ScheduleEntry entry :
            project.entries()) {

            double delayed =
                project.simulateDelay(
                    entry.activity().id(),
                    1.0
                );

            System.out.printf(
                "%-8s %-31s float=%5.1f " +
                "one-unit project impact=%4.1f%n",
                entry.activity().id(),
                entry.activity().name(),
                entry.totalFloat(),
                delayed - baseline
            );
        }
    }

    private static void demonstrateValidation() {
        System.out.println("\nVALIDATION");

        try {
            new ProjectSchedule(
                List.of(
                    new Activity(
                        "A",
                        "Requirements",
                        2,
                        List.of()
                    ),
                    new Activity(
                        "B",
                        "Implementation",
                        3,
                        List.of("UNKNOWN")
                    )
                )
            );
        }
        catch (IllegalArgumentException exception) {
            System.out.println(
                "Unknown dependency rejected: " +
                exception.getMessage()
            );
        }

        try {
            new ProjectSchedule(
                List.of(
                    new Activity(
                        "A",
                        "First",
                        2,
                        List.of("B")
                    ),
                    new Activity(
                        "B",
                        "Second",
                        3,
                        List.of("A")
                    )
                )
            );
        }
        catch (IllegalArgumentException exception) {
            System.out.println(
                "Circular dependency rejected: " +
                exception.getMessage()
            );
        }
    }

    public static void main(String[] args) {
        ProjectSchedule project =
            new ProjectSchedule(
                createEnterpriseRelease()
            );

        project.calculate();

        SchedulePolicy policy =
            new ZeroFloatPolicy();

        printSchedule(project, policy);
        demonstrateDelayAnalysis(project);
        demonstrateValidation();

        System.out.println("\nDOMAIN INTERPRETATION");
        System.out.println(
            "The scheduling engine calculates timing; the policy " +
            "interprets zero float as criticality."
        );
        System.out.println(
            "A critical activity is schedule-sensitive under the " +
            "current dependency and duration assumptions."
        );
        System.out.println(
            "The classification must be recalculated when activity " +
            "durations or dependencies change."
        );
    }
}
