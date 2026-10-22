import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

public class QualityPlanningEnterprise {

    enum RequirementState {
        PLANNED,
        VERIFIED,
        FAILED,
        DEFERRED
    }

    enum RiskLevel {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }

    enum GateDecision {
        PASS,
        BLOCKED
    }

    record QualityRequirement(
        String id,
        String description,
        String metric,
        double target,
        int priority,
        String verificationMethod
    ) {
        QualityRequirement {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("Requirement ID is required.");
            }
            if (description == null || description.isBlank()) {
                throw new IllegalArgumentException("Requirement description is required.");
            }
            if (metric == null || metric.isBlank()) {
                throw new IllegalArgumentException("Requirement metric is required.");
            }
            if (target < 0 || target > 100) {
                throw new IllegalArgumentException("Target must be between 0 and 100.");
            }
            if (priority < 1 || priority > 5) {
                throw new IllegalArgumentException("Priority must be between 1 and 5.");
            }
        }
    }

    record QualityEvidence(
        String requirementId,
        double observedValue,
        boolean passed,
        String evidence
    ) {
        QualityEvidence {
            if (requirementId == null || requirementId.isBlank()) {
                throw new IllegalArgumentException("Requirement ID is required.");
            }
            if (observedValue < 0 || observedValue > 100) {
                throw new IllegalArgumentException(
                    "Observed value must be between 0 and 100."
                );
            }
            if (evidence == null || evidence.isBlank()) {
                throw new IllegalArgumentException("Evidence description is required.");
            }
        }
    }

    record QualityRisk(
        String id,
        String description,
        double probability,
        double impact,
        String mitigation
    ) {
        QualityRisk {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException("Risk ID is required.");
            }
            if (probability < 0 || probability > 1 ||
                impact < 0 || impact > 1) {
                throw new IllegalArgumentException(
                    "Risk probability and impact must be between 0 and 1."
                );
            }
        }

        double score() {
            return probability * impact;
        }

        RiskLevel level() {
            if (score() >= 0.75) return RiskLevel.CRITICAL;
            if (score() >= 0.50) return RiskLevel.HIGH;
            if (score() >= 0.25) return RiskLevel.MEDIUM;
            return RiskLevel.LOW;
        }
    }

    static final class QualityPlan {
        private final String projectName;
        private final Map<String, QualityRequirement> requirements =
            new LinkedHashMap<>();
        private final Map<String, List<QualityEvidence>> evidence =
            new LinkedHashMap<>();
        private final List<QualityRisk> risks = new ArrayList<>();

        QualityPlan(String projectName) {
            this.projectName = Objects.requireNonNull(projectName);
            if (projectName.isBlank()) {
                throw new IllegalArgumentException("Project name cannot be blank.");
            }
        }

        void addRequirement(QualityRequirement requirement) {
            if (requirements.containsKey(requirement.id())) {
                throw new IllegalArgumentException(
                    "Duplicate requirement: " + requirement.id()
                );
            }

            requirements.put(requirement.id(), requirement);
            evidence.put(requirement.id(), new ArrayList<>());
        }

        void addEvidence(QualityEvidence item) {
            if (!requirements.containsKey(item.requirementId())) {
                throw new IllegalArgumentException(
                    "Unknown requirement: " + item.requirementId()
                );
            }

            evidence.get(item.requirementId()).add(item);
        }

        void addRisk(QualityRisk risk) {
            risks.add(risk);
        }

        Optional<QualityEvidence> latestEvidence(String requirementId) {
            return evidence.getOrDefault(requirementId, List.of())
                .stream()
                .reduce((first, second) -> second);
        }

        double readinessScore() {
            if (requirements.isEmpty()) {
                return 0.0;
            }

            double weightedScore = 0.0;
            int totalWeight = 0;

            for (QualityRequirement requirement : requirements.values()) {
                Optional<QualityEvidence> latest =
                    latestEvidence(requirement.id());

                if (latest.isEmpty()) {
                    continue;
                }

                double achievement = Math.min(
                    latest.get().observedValue() / requirement.target(),
                    1.0
                );

                weightedScore += achievement * requirement.priority();
                totalWeight += requirement.priority();
            }

            return totalWeight == 0
                ? 0.0
                : (weightedScore / totalWeight) * 100.0;
        }

        GateDecision evaluateGate() {
            for (QualityRequirement requirement : requirements.values()) {
                Optional<QualityEvidence> latest =
                    latestEvidence(requirement.id());

                if (latest.isEmpty() || !latest.get().passed()) {
                    return GateDecision.BLOCKED;
                }
            }

            boolean hasCriticalRisk = risks.stream()
                .anyMatch(risk -> risk.level() == RiskLevel.CRITICAL);

            return hasCriticalRisk
                ? GateDecision.BLOCKED
                : GateDecision.PASS;
        }

        void printReport() {
            System.out.printf(
                "Project: %s%nQuality readiness: %.2f%%%nGate: %s%n%n",
                projectName,
                readinessScore(),
                evaluateGate()
            );

            System.out.println("Requirements:");

            requirements.values().forEach(requirement -> {
                Optional<QualityEvidence> latest =
                    latestEvidence(requirement.id());

                String state;
                if (latest.isEmpty()) {
                    state = RequirementState.PLANNED.name();
                } else {
                    state = latest.get().passed()
                        ? RequirementState.VERIFIED.name()
                        : RequirementState.FAILED.name();
                }

                System.out.printf(
                    "  %s | target %.1f%% | %s%n",
                    requirement.id(),
                    requirement.target(),
                    state
                );
            });

            System.out.println("\nRisk register:");

            risks.stream()
                .sorted(Comparator.comparingDouble(QualityRisk::score).reversed())
                .forEach(risk ->
                    System.out.printf(
                        "  %s | %.2f | %s | %s%n",
                        risk.id(),
                        risk.score(),
                        risk.level(),
                        risk.mitigation()
                    )
                );
        }
    }

    public static void main(String[] args) {
        QualityPlan plan =
            new QualityPlan("Enterprise Customer Identity Service");

        plan.addRequirement(new QualityRequirement(
            "QR-201",
            "Identity-critical workflows must have adequate automated coverage.",
            "test_coverage",
            90,
            5,
            "CI coverage report"
        ));

        plan.addRequirement(new QualityRequirement(
            "QR-202",
            "Authentication operations must satisfy the response-time objective.",
            "latency_compliance",
            95,
            5,
            "Load test"
        ));

        plan.addRequirement(new QualityRequirement(
            "QR-203",
            "No unresolved critical security defects may remain.",
            "critical_defect_free",
            100,
            5,
            "Security audit"
        ));

        plan.addRequirement(new QualityRequirement(
            "QR-204",
            "Authorization validation must pass all mandatory policy tests.",
            "authorization_validation",
            100,
            4,
            "Security regression suite"
        ));

        plan.addEvidence(new QualityEvidence(
            "QR-201",
            94,
            true,
            "CI run reported 94% coverage."
        ));

        plan.addEvidence(new QualityEvidence(
            "QR-202",
            97,
            true,
            "Performance test satisfied the latency objective."
        ));

        plan.addEvidence(new QualityEvidence(
            "QR-203",
            100,
            true,
            "Security audit found no critical defects."
        ));

        plan.addEvidence(new QualityEvidence(
            "QR-204",
            98,
            false,
            "Two authorization boundary cases failed."
        ));

        plan.addRisk(new QualityRisk(
            "R-201",
            "Privilege-boundary defects may cause unauthorized access.",
            0.45,
            0.95,
            "Expand authorization boundary tests and negative cases."
        ));

        plan.addRisk(new QualityRisk(
            "R-202",
            "High authentication volume may degrade response time.",
            0.30,
            0.70,
            "Run load tests before each production release."
        ));

        plan.printReport();
    }
}
