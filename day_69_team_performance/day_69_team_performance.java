import java.time.LocalDate;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Enterprise Team Performance Management System.
 *
 * Features:
 * - Team performance measurement
 * - Configurable evaluation policies
 * - Weighted performance scoring
 * - Historical performance analysis
 * - Review and improvement workflows
 * - Evaluation state management
 * - Organizational reporting
 *
 * Java 17, no external dependencies.
 */
public class TeamPerformance {

    enum Metric {
        GOAL_ACHIEVEMENT,
        PRODUCTIVITY,
        WORK_QUALITY,
        COLLABORATION,
        RELIABILITY,
        DELIVERY_CONSISTENCY
    }

    enum PerformanceBand {
        EXCELLENT,
        STRONG,
        SATISFACTORY,
        NEEDS_IMPROVEMENT,
        CRITICAL
    }

    enum ActionStatus {
        OPEN,
        IN_PROGRESS,
        COMPLETED,
        CANCELLED
    }

    enum EvaluationStatus {
        PENDING,
        COMPLETED,
        FAILED
    }

    static class ValidationException extends RuntimeException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class EvaluationException extends RuntimeException {
        EvaluationException(String message) {
            super(message);
        }
    }

    record TeamMetrics(Map<Metric, Double> values) {

        TeamMetrics {
            Objects.requireNonNull(values, "Metrics are required.");

            EnumMap<Metric, Double> copy =
                new EnumMap<>(Metric.class);

            for (Metric metric : Metric.values()) {
                Double value = values.get(metric);

                if (value == null ||
                    !Double.isFinite(value) ||
                    value < 0 ||
                    value > 100) {
                    throw new ValidationException(
                        "Invalid metric: " + metric
                    );
                }

                copy.put(metric, value);
            }

            if (values.size() != Metric.values().length) {
                throw new ValidationException(
                    "Unexpected performance metrics."
                );
            }

            values = Map.copyOf(copy);
        }

        double get(Metric metric) {
            return values.get(metric);
        }
    }

    record Team(
        String id,
        String name,
        String department,
        String manager,
        int members,
        String period,
        TeamMetrics metrics
    ) {

        Team {
            if (id == null || id.isBlank() ||
                name == null || name.isBlank() ||
                department == null || department.isBlank() ||
                manager == null || manager.isBlank() ||
                period == null || period.isBlank()) {
                throw new ValidationException(
                    "Team identity information is required."
                );
            }

            if (members <= 0) {
                throw new ValidationException(
                    "Team must contain at least one member."
                );
            }

            Objects.requireNonNull(metrics);
        }
    }

    record EvaluationPolicy(Map<Metric, Double> weights) {

        EvaluationPolicy {
            Objects.requireNonNull(weights);

            EnumMap<Metric, Double> copy =
                new EnumMap<>(Metric.class);

            double total = 0;

            for (Metric metric : Metric.values()) {
                Double weight = weights.get(metric);

                if (weight == null ||
                    !Double.isFinite(weight) ||
                    weight < 0 ||
                    weight > 1) {
                    throw new ValidationException(
                        "Invalid weight for " + metric
                    );
                }

                copy.put(metric, weight);
                total += weight;
            }

            if (weights.size() != Metric.values().length ||
                Math.abs(total - 1.0) > 0.000001) {
                throw new ValidationException(
                    "All weights must be present and total 1.0."
                );
            }

            weights = Map.copyOf(copy);
        }

        static EvaluationPolicy standard() {
            EnumMap<Metric, Double> weights =
                new EnumMap<>(Metric.class);

            weights.put(Metric.GOAL_ACHIEVEMENT, 0.25);
            weights.put(Metric.PRODUCTIVITY, 0.20);
            weights.put(Metric.WORK_QUALITY, 0.20);
            weights.put(Metric.COLLABORATION, 0.15);
            weights.put(Metric.RELIABILITY, 0.10);
            weights.put(Metric.DELIVERY_CONSISTENCY, 0.10);

            return new EvaluationPolicy(weights);
        }

        double calculate(TeamMetrics metrics) {
            double score = 0;

            for (Metric metric : Metric.values()) {
                score += metrics.get(metric) * weights.get(metric);
            }

            return Math.round(score * 100.0) / 100.0;
        }
    }

    record EvaluationResult(
        String evaluationId,
        String teamId,
        String teamName,
        String period,
        double score,
        PerformanceBand band,
        EvaluationStatus status,
        List<Metric> strengths,
        List<Metric> improvementAreas,
        Double previousScore,
        String trend,
        Instant evaluatedAt
    ) {
        EvaluationResult {
            strengths = List.copyOf(strengths);
            improvementAreas = List.copyOf(improvementAreas);
        }
    }

    record HistoricalEvaluation(
        String teamId,
        String period,
        double score,
        Instant evaluatedAt
    ) {}

    record ImprovementAction(
        String id,
        String teamId,
        Metric metric,
        String description,
        String owner,
        LocalDate dueDate,
        ActionStatus status,
        Instant createdAt
    ) {}

    interface EvaluationRepository {
        void save(EvaluationResult result);
        List<EvaluationResult> findAll();
    }

    static class InMemoryEvaluationRepository
        implements EvaluationRepository {

        private final Map<String, EvaluationResult> evaluations =
            new HashMap<>();

        @Override
        public synchronized void save(EvaluationResult result) {
            String key = result.teamId() + ":" + result.period();

            if (evaluations.values().stream().anyMatch(
                existing ->
                    (existing.teamId() + ":" + existing.period()).equals(key)
                    && !existing.evaluationId().equals(result.evaluationId())
            )) {
                throw new EvaluationException(
                    "An evaluation already exists for this team and period."
                );
            }

            evaluations.put(result.evaluationId(), result);
        }

        @Override
        public synchronized List<EvaluationResult> findAll() {
            return List.copyOf(evaluations.values());
        }
    }

    static class ImprovementService {

        private final Map<String, ImprovementAction> actions =
            new HashMap<>();

        public synchronized ImprovementAction create(
            String teamId,
            Metric metric,
            String description,
            String owner,
            LocalDate dueDate
        ) {
            if (teamId == null || teamId.isBlank() ||
                description == null || description.isBlank() ||
                owner == null || owner.isBlank()) {
                throw new ValidationException(
                    "Improvement action fields are required."
                );
            }

            Objects.requireNonNull(metric);
            Objects.requireNonNull(dueDate);

            if (dueDate.isBefore(LocalDate.now())) {
                throw new ValidationException(
                    "Due date cannot be in the past."
                );
            }

            String id = UUID.randomUUID().toString();

            ImprovementAction action = new ImprovementAction(
                id,
                teamId,
                metric,
                description,
                owner,
                dueDate,
                ActionStatus.OPEN,
                Instant.now()
            );

            actions.put(id, action);

            return action;
        }

        public synchronized ImprovementAction updateStatus(
            String actionId,
            ActionStatus newStatus
        ) {
            ImprovementAction current = actions.get(actionId);

            if (current == null) {
                throw new ValidationException("Action not found.");
            }

            if (current.status() == ActionStatus.COMPLETED ||
                current.status() == ActionStatus.CANCELLED) {
                throw new ValidationException(
                    "Cannot modify a terminal action."
                );
            }

            ImprovementAction updated = new ImprovementAction(
                current.id(),
                current.teamId(),
                current.metric(),
                current.description(),
                current.owner(),
                current.dueDate(),
                newStatus,
                current.createdAt()
            );

            actions.put(actionId, updated);

            return updated;
        }

        public synchronized List<ImprovementAction> findByTeam(
            String teamId
        ) {
            return actions.values().stream()
                .filter(action -> action.teamId().equals(teamId))
                .toList();
        }
    }

    static class PerformanceService {

        private final EvaluationPolicy policy;
        private final EvaluationRepository repository;

        private final Map<String, Team> teams = new HashMap<>();

        private final Map<String, List<HistoricalEvaluation>> history =
            new HashMap<>();

        PerformanceService(
            EvaluationPolicy policy,
            EvaluationRepository repository
        ) {
            this.policy = Objects.requireNonNull(policy);
            this.repository = Objects.requireNonNull(repository);
        }

        public synchronized void registerTeam(Team team) {
            Objects.requireNonNull(team);

            if (teams.containsKey(team.id())) {
                throw new ValidationException(
                    "Team already registered."
                );
            }

            teams.put(team.id(), team);
        }

        public synchronized void updateMetrics(
            String teamId,
            TeamMetrics metrics
        ) {
            Team current = teams.get(teamId);

            if (current == null) {
                throw new ValidationException("Team not found.");
            }

            Team updated = new Team(
                current.id(),
                current.name(),
                current.department(),
                current.manager(),
                current.members(),
                current.period(),
                metrics
            );

            teams.put(teamId, updated);
        }

        public synchronized void recordHistoricalEvaluation(
            String teamId,
            String period,
            double score
        ) {
            if (!teams.containsKey(teamId)) {
                throw new ValidationException("Unknown team.");
            }

            if (!Double.isFinite(score) || score < 0 || score > 100) {
                throw new ValidationException("Invalid historical score.");
            }

            List<HistoricalEvaluation> records =
                history.computeIfAbsent(
                    teamId,
                    key -> new ArrayList<>()
                );

            if (records.stream().anyMatch(
                item -> item.period().equals(period)
            )) {
                throw new ValidationException(
                    "Historical period already recorded."
                );
            }

            records.add(new HistoricalEvaluation(
                teamId,
                period,
                score,
                Instant.now()
            ));
        }

        public synchronized EvaluationResult evaluate(String teamId) {
            Team team = teams.get(teamId);

            if (team == null) {
                throw new EvaluationException("Team not found.");
            }

            double score = policy.calculate(team.metrics());

            List<Metric> strengths = new ArrayList<>();
            List<Metric> improvementAreas = new ArrayList<>();

            for (Metric metric : Metric.values()) {
                double value = team.metrics().get(metric);

                if (value >= 85) {
                    strengths.add(metric);
                }

                if (value < 70) {
                    improvementAreas.add(metric);
                }
            }

            List<HistoricalEvaluation> records =
                history.getOrDefault(teamId, List.of());

            Double previous = records.stream()
                .filter(record ->
                    record.period().compareTo(team.period()) < 0
                )
                .max(Comparator.comparing(
                    HistoricalEvaluation::period
                ))
                .map(HistoricalEvaluation::score)
                .orElse(null);

            String trend = previous == null
                ? "Not Available"
                : score > previous ? "Improving"
                : score < previous ? "Declining"
                : "Stable";

            EvaluationResult result = new EvaluationResult(
                UUID.randomUUID().toString(),
                team.id(),
                team.name(),
                team.period(),
                score,
                classify(score),
                EvaluationStatus.COMPLETED,
                strengths,
                improvementAreas,
                previous,
                trend,
                Instant.now()
            );

            repository.save(result);

            return result;
        }

        public synchronized List<EvaluationResult> evaluateAll() {
            List<EvaluationResult> results = new ArrayList<>();

            for (String teamId : teams.keySet()) {
                results.add(evaluate(teamId));
            }

            results.sort(
                Comparator.comparingDouble(
                    EvaluationResult::score
                ).reversed()
            );

            return List.copyOf(results);
        }

        public List<EvaluationResult> getEvaluations() {
            return repository.findAll();
        }
    }

    static class ReportingService {

        public static void printReport(
            List<EvaluationResult> evaluations
        ) {
            System.out.println("\nENTERPRISE TEAM PERFORMANCE REPORT");
            System.out.println("=".repeat(90));

            System.out.printf(
                "%-22s %-12s %-24s %-16s%n",
                "Team",
                "Score",
                "Performance",
                "Trend"
            );

            System.out.println("-".repeat(90));

            for (EvaluationResult result : evaluations) {
                System.out.printf(
                    "%-22s %-12.2f %-24s %-16s%n",
                    result.teamName(),
                    result.score(),
                    result.band(),
                    result.trend()
                );

                System.out.println(
                    "  Strengths: " + result.strengths()
                );

                System.out.println(
                    "  Improvement areas: " +
                    result.improvementAreas()
                );
            }

            double average = evaluations.stream()
                .mapToDouble(EvaluationResult::score)
                .average()
                .orElse(0);

            System.out.printf(
                "%nOrganization average: %.2f%n",
                average
            );

            Map<PerformanceBand, Long> distribution =
                evaluations.stream().collect(
                    Collectors.groupingBy(
                        EvaluationResult::band,
                        () -> new EnumMap<>(PerformanceBand.class),
                        Collectors.counting()
                    )
                );

            System.out.println("Performance distribution: " + distribution);
        }
    }

    static PerformanceBand classify(double score) {
        if (score >= 90) return PerformanceBand.EXCELLENT;
        if (score >= 80) return PerformanceBand.STRONG;
        if (score >= 70) return PerformanceBand.SATISFACTORY;
        if (score >= 60) return PerformanceBand.NEEDS_IMPROVEMENT;

        return PerformanceBand.CRITICAL;
    }

    static Team createTeam(
        String id,
        String name,
        String department,
        String manager,
        int members,
        String period,
        double... scores
    ) {
        if (scores.length != Metric.values().length) {
            throw new ValidationException(
                "Exactly six metric values are required."
            );
        }

        EnumMap<Metric, Double> values =
            new EnumMap<>(Metric.class);

        int index = 0;

        for (Metric metric : Metric.values()) {
            values.put(metric, scores[index++]);
        }

        return new Team(
            id,
            name,
            department,
            manager,
            members,
            period,
            new TeamMetrics(values)
        );
    }

    public static void main(String[] args) {
        try {
            EvaluationRepository repository =
                new InMemoryEvaluationRepository();

            PerformanceService service = new PerformanceService(
                EvaluationPolicy.standard(),
                repository
            );

            service.registerTeam(createTeam(
                "T001", "Engineering", "Technology",
                "Manager A", 12, "2026-Q4",
                92, 88, 95, 85, 90, 87
            ));

            service.registerTeam(createTeam(
                "T002", "Customer Support", "Operations",
                "Manager B", 10, "2026-Q4",
                78, 85, 82, 91, 88, 80
            ));

            service.registerTeam(createTeam(
                "T003", "Research", "R&D",
                "Manager C", 8, "2026-Q4",
                95, 72, 90, 80, 75, 78
            ));

            service.registerTeam(createTeam(
                "T004", "Quality Assurance", "Technology",
                "Manager D", 6, "2026-Q4",
                65, 68, 92, 75, 70, 62
            ));

            service.recordHistoricalEvaluation(
                "T001", "2026-Q3", 84
            );

            service.recordHistoricalEvaluation(
                "T002", "2026-Q3", 82
            );

            service.recordHistoricalEvaluation(
                "T003", "2026-Q3", 80
            );

            service.recordHistoricalEvaluation(
                "T004", "2026-Q3", 70
            );

            List<EvaluationResult> results =
                service.evaluateAll();

            ReportingService.printReport(results);

            ImprovementService improvementService =
                new ImprovementService();

            ImprovementAction action = improvementService.create(
                "T003",
                Metric.PRODUCTIVITY,
                "Improve research planning and task estimation.",
                "Research Manager",
                LocalDate.of(2026, 12, 15)
            );

            System.out.println("\nIMPROVEMENT ACTION");
            System.out.println(action);

            System.out.println("\nEVALUATION RECORDS");
            System.out.println(service.getEvaluations().size());

        } catch (ValidationException | EvaluationException error) {
            System.err.println(
                "Performance management error: " + error.getMessage()
            );

            System.exitCode = 1;
        }
    }
}
