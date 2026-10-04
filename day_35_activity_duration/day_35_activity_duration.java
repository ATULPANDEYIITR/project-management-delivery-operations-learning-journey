import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Random;
import java.util.Set;

/*
 * Enterprise Activity Duration Estimation Service
 *
 * The domain model separates:
 * - the activity being estimated,
 * - uncertainty around its duration,
 * - historical calibration,
 * - dependency constraints,
 * - schedule calculation,
 * - and estimation-quality measurement.
 *
 * Java records are used for immutable value objects where state should not
 * change after construction. The service layer owns estimation rules.
 */

public class ActivityDurationEstimator {

    enum ActivityType {
        ANALYSIS,
        IMPLEMENTATION,
        TESTING,
        DOCUMENTATION,
        INTEGRATION
    }

    record DurationEstimate(
        double optimistic,
        double mostLikely,
        double pessimistic
    ) {
        DurationEstimate {
            if (!Double.isFinite(optimistic)
                || !Double.isFinite(mostLikely)
                || !Double.isFinite(pessimistic)) {
                throw new IllegalArgumentException(
                    "All durations must be finite."
                );
            }

            if (optimistic < 0
                || mostLikely < 0
                || pessimistic < 0) {
                throw new IllegalArgumentException(
                    "Duration cannot be negative."
                );
            }

            if (!(optimistic <= mostLikely
                && mostLikely <= pessimistic)) {
                throw new IllegalArgumentException(
                    "Expected optimistic <= mostLikely <= pessimistic."
                );
            }
        }

        double pertExpected() {
            return (
                optimistic +
                4 * mostLikely +
                pessimistic
            ) / 6.0;
        }

        double standardDeviation() {
            return (pessimistic - optimistic) / 6.0;
        }
    }

    record HistoricalDuration(
        ActivityType type,
        double estimatedHours,
        double actualHours
    ) {
        HistoricalDuration {
            Objects.requireNonNull(type, "Activity type is required.");

            if (estimatedHours <= 0 || actualHours < 0) {
                throw new IllegalArgumentException(
                    "Historical durations contain invalid values."
                );
            }
        }
    }

    record Activity(
        String name,
        ActivityType type,
        DurationEstimate estimate,
        List<String> dependencies
    ) {
        Activity {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Activity name cannot be blank."
                );
            }

            Objects.requireNonNull(type);
            Objects.requireNonNull(estimate);

            dependencies = List.copyOf(dependencies);
        }
    }

    record ScheduleEntry(
        String activityName,
        double startHour,
        double finishHour
    ) {}

    static final class HistoricalCalibrator {
        private final List<HistoricalDuration> observations;

        HistoricalCalibrator(List<HistoricalDuration> observations) {
            if (observations.isEmpty()) {
                throw new IllegalArgumentException(
                    "Historical observations cannot be empty."
                );
            }

            this.observations = List.copyOf(observations);
        }

        double globalFactor() {
            double estimated = 0;
            double actual = 0;

            for (HistoricalDuration observation : observations) {
                estimated += observation.estimatedHours();
                actual += observation.actualHours();
            }

            return actual / estimated;
        }

        double factorFor(ActivityType type) {
            double estimated = 0;
            double actual = 0;

            for (HistoricalDuration observation : observations) {
                if (observation.type() == type) {
                    estimated += observation.estimatedHours();
                    actual += observation.actualHours();
                }
            }

            return estimated == 0
                ? globalFactor()
                : actual / estimated;
        }

        double calibrated(Activity activity) {
            return activity.estimate().pertExpected()
                * factorFor(activity.type());
        }
    }

    static final class DependencyResolver {
        private final Map<String, Activity> activities;

        DependencyResolver(List<Activity> activityList) {
            this.activities = new HashMap<>();

            for (Activity activity : activityList) {
                if (activities.put(activity.name(), activity) != null) {
                    throw new IllegalArgumentException(
                        "Duplicate activity: " + activity.name()
                    );
                }
            }

            validateDependencyReferences();
        }

        private void validateDependencyReferences() {
            for (Activity activity : activities.values()) {
                for (String dependency : activity.dependencies()) {
                    if (!activities.containsKey(dependency)) {
                        throw new IllegalArgumentException(
                            "Unknown dependency '" +
                            dependency +
                            "' for activity '" +
                            activity.name() +
                            "'."
                        );
                    }
                }
            }
        }

        List<Activity> topologicalOrder() {
            Map<String, Integer> state = new HashMap<>();
            List<Activity> result = new ArrayList<>();

            for (String name : activities.keySet()) {
                visit(name, state, result);
            }

            return result;
        }

        private void visit(
            String name,
            Map<String, Integer> state,
            List<Activity> result
        ) {
            int current = state.getOrDefault(name, 0);

            if (current == 1) {
                throw new IllegalStateException(
                    "Circular dependency detected at " + name
                );
            }

            if (current == 2) {
                return;
            }

            state.put(name, 1);

            for (String dependency :
                activities.get(name).dependencies()) {
                visit(dependency, state, result);
            }

            state.put(name, 2);
            result.add(activities.get(name));
        }
    }

    static final class ScheduleService {
        private final HistoricalCalibrator calibrator;

        ScheduleService(HistoricalCalibrator calibrator) {
            this.calibrator = calibrator;
        }

        List<ScheduleEntry> calculate(List<Activity> activities) {
            DependencyResolver resolver =
                new DependencyResolver(activities);

            Map<String, Double> finishTimes = new HashMap<>();
            List<ScheduleEntry> schedule = new ArrayList<>();

            for (Activity activity :
                resolver.topologicalOrder()) {

                double start = 0;

                for (String dependency :
                    activity.dependencies()) {
                    start = Math.max(
                        start,
                        finishTimes.get(dependency)
                    );
                }

                double duration =
                    calibrator.calibrated(activity);

                double finish = start + duration;

                finishTimes.put(activity.name(), finish);

                schedule.add(
                    new ScheduleEntry(
                        activity.name(),
                        start,
                        finish
                    )
                );
            }

            return schedule;
        }
    }

    static final class MonteCarloService {
        private final Random random;

        MonteCarloService(long seed) {
            random = new Random(seed);
        }

        double simulateProject(List<Activity> activities) {
            DependencyResolver resolver =
                new DependencyResolver(activities);

            Map<String, Double> finishTimes = new HashMap<>();

            for (Activity activity :
                resolver.topologicalOrder()) {

                double start = 0;

                for (String dependency :
                    activity.dependencies()) {
                    start = Math.max(
                        start,
                        finishTimes.get(dependency)
                    );
                }

                double duration =
                    triangular(activity.estimate());

                finishTimes.put(
                    activity.name(),
                    start + duration
                );
            }

            return finishTimes.values()
                .stream()
                .max(Comparator.naturalOrder())
                .orElse(0.0);
        }

        private double triangular(DurationEstimate estimate) {
            double u = random.nextDouble();

            double a = estimate.optimistic();
            double b = estimate.mostLikely();
            double c = estimate.pessimistic();

            if (a == c) {
                return a;
            }

            double modePosition = (b - a) / (c - a);

            if (u < modePosition) {
                return a +
                    Math.sqrt(
                        u * (b - a) * (c - a)
                    );
            }

            return c -
                Math.sqrt(
                    (1 - u) *
                    (c - b) *
                    (c - a)
                );
        }

        List<Double> simulate(
            List<Activity> activities,
            int iterations
        ) {
            if (iterations <= 0) {
                throw new IllegalArgumentException(
                    "Iterations must be positive."
                );
            }

            List<Double> values = new ArrayList<>();

            for (int i = 0; i < iterations; i++) {
                values.add(simulateProject(activities));
            }

            return values;
        }
    }

    record EstimationMetrics(
        double meanAbsoluteError,
        double meanAbsolutePercentageError,
        double signedBias
    ) {}

    static EstimationMetrics quality(
        List<Double> estimated,
        List<Double> actual
    ) {
        if (estimated.isEmpty()
            || estimated.size() != actual.size()) {
            throw new IllegalArgumentException(
                "Estimated and actual samples must have equal non-zero size."
            );
        }

        double absoluteError = 0;
        double percentageError = 0;
        double bias = 0;
        int percentageSamples = 0;

        for (int i = 0; i < estimated.size(); i++) {
            double error = actual.get(i) - estimated.get(i);

            absoluteError += Math.abs(error);
            bias += error;

            if (estimated.get(i) > 0) {
                percentageError +=
                    Math.abs(error) / estimated.get(i);
                percentageSamples++;
            }
        }

        return new EstimationMetrics(
            absoluteError / estimated.size(),
            percentageError / percentageSamples * 100,
            bias / estimated.size()
        );
    }

    static void printHeader(String title) {
        System.out.println();
        System.out.println("=".repeat(78));
        System.out.println(title);
        System.out.println("=".repeat(78));
    }

    static double percentile(
        List<Double> values,
        double percentage
    ) {
        if (values.isEmpty()) {
            throw new IllegalArgumentException(
                "No simulation results."
            );
        }

        List<Double> sorted = new ArrayList<>(values);
        sorted.sort(Double::compareTo);

        double position =
            (sorted.size() - 1) * percentage / 100.0;

        int lower = (int) Math.floor(position);
        int upper = (int) Math.ceil(position);

        if (lower == upper) {
            return sorted.get(lower);
        }

        double fraction = position - lower;

        return sorted.get(lower)
            + (sorted.get(upper) - sorted.get(lower))
            * fraction;
    }

    public static void main(String[] args) {
        printHeader("Enterprise Activity Duration Estimation");

        List<HistoricalDuration> history = List.of(
            new HistoricalDuration(
                ActivityType.ANALYSIS, 6, 8
            ),
            new HistoricalDuration(
                ActivityType.ANALYSIS, 10, 11
            ),
            new HistoricalDuration(
                ActivityType.IMPLEMENTATION, 14, 19
            ),
            new HistoricalDuration(
                ActivityType.IMPLEMENTATION, 20, 24
            ),
            new HistoricalDuration(
                ActivityType.TESTING, 10, 9
            ),
            new HistoricalDuration(
                ActivityType.TESTING, 15, 18
            ),
            new HistoricalDuration(
                ActivityType.INTEGRATION, 9, 13
            ),
            new HistoricalDuration(
                ActivityType.INTEGRATION, 12, 16
            )
        );

        HistoricalCalibrator calibrator =
            new HistoricalCalibrator(history);

        System.out.printf(
            "Global historical factor: %.3f%n",
            calibrator.globalFactor()
        );

        List<Activity> activities = List.of(
            new Activity(
                "Requirements analysis",
                ActivityType.ANALYSIS,
                new DurationEstimate(3, 5, 9),
                List.of()
            ),
            new Activity(
                "Backend implementation",
                ActivityType.IMPLEMENTATION,
                new DurationEstimate(12, 18, 30),
                List.of("Requirements analysis")
            ),
            new Activity(
                "Frontend implementation",
                ActivityType.IMPLEMENTATION,
                new DurationEstimate(10, 15, 26),
                List.of("Requirements analysis")
            ),
            new Activity(
                "Backend verification",
                ActivityType.TESTING,
                new DurationEstimate(5, 8, 15),
                List.of("Backend implementation")
            ),
            new Activity(
                "Frontend verification",
                ActivityType.TESTING,
                new DurationEstimate(4, 7, 13),
                List.of("Frontend implementation")
            ),
            new Activity(
                "System integration",
                ActivityType.INTEGRATION,
                new DurationEstimate(6, 10, 18),
                List.of(
                    "Backend verification",
                    "Frontend verification"
                )
            )
        );

        printHeader("Calibrated Activity Estimates");

        for (Activity activity : activities) {
            System.out.printf(
                "%-28s PERT=%6.2f h calibrated=%6.2f h%n",
                activity.name(),
                activity.estimate().pertExpected(),
                calibrator.calibrated(activity)
            );
        }

        printHeader("Dependency-Aware Schedule");

        ScheduleService scheduleService =
            new ScheduleService(calibrator);

        List<ScheduleEntry> schedule =
            scheduleService.calculate(activities);

        for (ScheduleEntry entry : schedule) {
            System.out.printf(
                "%-28s start=%6.2f finish=%6.2f h%n",
                entry.activityName(),
                entry.startHour(),
                entry.finishHour()
            );
        }

        double expectedFinish = schedule.stream()
            .mapToDouble(ScheduleEntry::finishHour)
            .max()
            .orElse(0);

        System.out.printf(
            "%nExpected elapsed project duration: %.2f h%n",
            expectedFinish
        );

        printHeader("Monte Carlo Schedule Risk");

        MonteCarloService simulation =
            new MonteCarloService(20261005);

        List<Double> simulations =
            simulation.simulate(activities, 20000);

        System.out.printf(
            "Median: %.2f h%n",
            percentile(simulations, 50)
        );

        System.out.printf(
            "80th percentile: %.2f h%n",
            percentile(simulations, 80)
        );

        System.out.printf(
            "90th percentile: %.2f h%n",
            percentile(simulations, 90)
        );

        System.out.printf(
            "95th percentile: %.2f h%n",
            percentile(simulations, 95)
        );

        printHeader("Historical Estimation Quality");

        EstimationMetrics metrics = quality(
            List.of(8.0, 12.0, 16.0, 10.0, 20.0),
            List.of(9.0, 15.0, 13.0, 11.0, 24.0)
        );

        System.out.printf(
            "Mean absolute error: %.2f h%n",
            metrics.meanAbsoluteError()
        );

        System.out.printf(
            "Mean absolute percentage error: %.2f%%%n",
            metrics.meanAbsolutePercentageError()
        );

        System.out.printf(
            "Signed bias: %.2f h%n",
            metrics.signedBias()
        );

        printHeader("Failure-State Demonstration");

        try {
            new DurationEstimate(10, 7, 20);
        } catch (IllegalArgumentException error) {
            System.out.println(
                "Invalid estimate rejected: " +
                error.getMessage()
            );
        }

        try {
            List<Activity> circular = List.of(
                new Activity(
                    "A",
                    ActivityType.IMPLEMENTATION,
                    new DurationEstimate(1, 2, 4),
                    List.of("B")
                ),
                new Activity(
                    "B",
                    ActivityType.TESTING,
                    new DurationEstimate(1, 2, 4),
                    List.of("A")
                )
            );

            new DependencyResolver(circular).topologicalOrder();
        } catch (IllegalStateException error) {
            System.out.println(
                "Circular dependency rejected: " +
                error.getMessage()
            );
        }

        printHeader("Domain Interpretation");

        System.out.println(
            "The DurationEstimate represents uncertainty for one activity."
        );
        System.out.println(
            "HistoricalCalibrator adjusts estimates using observed durations."
        );
        System.out.println(
            "DependencyResolver determines which activities can start."
        );
        System.out.println(
            "ScheduleService converts activity durations into elapsed time."
        );
        System.out.println(
            "MonteCarloService converts uncertain activity durations into"
        );
        System.out.println(
            "a distribution of possible project completion times."
        );
    }
}
