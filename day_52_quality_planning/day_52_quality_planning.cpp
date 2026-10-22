#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

enum class RiskLevel {
    Low,
    Medium,
    High,
    Critical
};

enum class MergeDecision {
    Eligible,
    Blocked
};

struct QualityRequirement {
    std::string id;
    std::string description;
    std::string metric;
    double target;
    int priority;
    std::string verificationMethod;
};

struct QualityEvidence {
    std::string requirementId;
    double observedValue;
    bool passed;
    std::string evidence;
};

struct QualityRisk {
    std::string id;
    std::string description;
    double probability;
    double impact;
    std::string mitigation;

    double score() const {
        return probability * impact;
    }

    RiskLevel level() const {
        const double value = score();
        if (value >= 0.75) return RiskLevel::Critical;
        if (value >= 0.50) return RiskLevel::High;
        if (value >= 0.25) return RiskLevel::Medium;
        return RiskLevel::Low;
    }
};

class QualityGovernanceEngine {
private:
    std::map<std::string, QualityRequirement> requirements_;
    std::vector<QualityEvidence> evidence_;
    std::vector<QualityRisk> risks_;

    static void validatePercentage(double value, const std::string& name) {
        if (value < 0.0 || value > 100.0) {
            throw std::invalid_argument(name + " must be between 0 and 100.");
        }
    }

public:
    void addRequirement(const QualityRequirement& requirement) {
        validatePercentage(requirement.target, "Requirement target");

        if (requirement.id.empty() || requirement.description.empty()) {
            throw std::invalid_argument("Requirement identity and description are required.");
        }

        if (requirement.priority < 1 || requirement.priority > 5) {
            throw std::invalid_argument("Requirement priority must be between 1 and 5.");
        }

        if (requirements_.contains(requirement.id)) {
            throw std::invalid_argument("Duplicate requirement ID: " + requirement.id);
        }

        requirements_.emplace(requirement.id, requirement);
    }

    void recordEvidence(const QualityEvidence& evidence) {
        validatePercentage(evidence.observedValue, "Observed value");

        if (!requirements_.contains(evidence.requirementId)) {
            throw std::invalid_argument(
                "Evidence references unknown requirement: " + evidence.requirementId
            );
        }

        evidence_.push_back(evidence);
    }

    void addRisk(const QualityRisk& risk) {
        if (risk.probability < 0.0 || risk.probability > 1.0 ||
            risk.impact < 0.0 || risk.impact > 1.0) {
            throw std::invalid_argument(
                "Risk probability and impact must be between 0 and 1."
            );
        }

        risks_.push_back(risk);
    }

    std::optional<QualityEvidence> latestEvidence(
        const std::string& requirementId
    ) const {
        // Evidence is append-only in this model, so the last matching
        // record represents the latest verification result.
        for (auto it = evidence_.rbegin(); it != evidence_.rend(); ++it) {
            if (it->requirementId == requirementId) {
                return *it;
            }
        }
        return std::nullopt;
    }

    double readinessScore() const {
        if (requirements_.empty()) {
            return 0.0;
        }

        double weightedAchievement = 0.0;
        int totalWeight = 0;

        for (const auto& [id, requirement] : requirements_) {
            const auto evidence = latestEvidence(id);
            if (!evidence) {
                continue;
            }

            const double achievement =
                std::min(evidence->observedValue / requirement.target, 1.0);

            weightedAchievement += achievement * requirement.priority;
            totalWeight += requirement.priority;
        }

        if (totalWeight == 0) {
            return 0.0;
        }

        return (weightedAchievement / totalWeight) * 100.0;
    }

    MergeDecision evaluateMergeEligibility() const {
        /*
         * This is a quality-gate decision, not a simple percentage check.
         * Missing evidence, failed mandatory evidence, and critical risks
         * block release even if the weighted score appears acceptable.
         */
        for (const auto& [id, requirement] : requirements_) {
            const auto evidence = latestEvidence(id);

            if (!evidence || !evidence->passed) {
                return MergeDecision::Blocked;
            }
        }

        for (const auto& risk : risks_) {
            if (risk.level() == RiskLevel::Critical) {
                return MergeDecision::Blocked;
            }
        }

        return MergeDecision::Eligible;
    }

    const std::vector<QualityRisk>& risks() const {
        return risks_;
    }

    const std::map<std::string, QualityRequirement>& requirements() const {
        return requirements_;
    }
};

std::string riskLevelName(RiskLevel level) {
    switch (level) {
        case RiskLevel::Low: return "LOW";
        case RiskLevel::Medium: return "MEDIUM";
        case RiskLevel::High: return "HIGH";
        case RiskLevel::Critical: return "CRITICAL";
    }
    return "UNKNOWN";
}

void printQualityReport(const QualityGovernanceEngine& engine) {
    std::cout << std::fixed << std::setprecision(2);
    std::cout << "Quality readiness score: "
              << engine.readinessScore() << "%\n";

    const auto decision = engine.evaluateMergeEligibility();
    std::cout << "Quality gate: "
              << (decision == MergeDecision::Eligible ? "PASS" : "BLOCKED")
              << "\n\n";

    std::cout << "Quality requirements:\n";

    for (const auto& [id, requirement] : engine.requirements()) {
        const auto evidence = engine.latestEvidence(id);

        std::cout << "  " << id
                  << " | target=" << requirement.target << "%"
                  << " | ";

        if (!evidence) {
            std::cout << "NO EVIDENCE\n";
        } else {
            std::cout << (evidence->passed ? "PASS" : "FAIL")
                      << " | observed=" << evidence->observedValue
                      << "%\n";
        }
    }

    std::cout << "\nQuality risks:\n";

    for (const auto& risk : engine.risks()) {
        std::cout << "  " << risk.id
                  << " | score=" << risk.score()
                  << " | level=" << riskLevelName(risk.level())
                  << " | mitigation=" << risk.mitigation
                  << "\n";
    }
}

int main() {
    try {
        QualityGovernanceEngine engine;

        engine.addRequirement({
            "QP-001",
            "Critical payment workflows require strong automated test coverage.",
            "test_coverage",
            90.0,
            5,
            "CI coverage report"
        });

        engine.addRequirement({
            "QP-002",
            "Critical transactions must meet the defined latency objective.",
            "latency_compliance",
            95.0,
            5,
            "Load test"
        });

        engine.addRequirement({
            "QP-003",
            "No critical data-integrity defects may remain before release.",
            "critical_defect_free",
            100.0,
            5,
            "Defect audit"
        });

        engine.addRequirement({
            "QP-004",
            "Security-sensitive input validation must satisfy all mandatory tests.",
            "security_validation",
            100.0,
            4,
            "Security regression suite"
        });

        engine.recordEvidence({
            "QP-001",
            92.0,
            true,
            "CI pipeline recorded 92% coverage."
        });

        engine.recordEvidence({
            "QP-002",
            96.0,
            true,
            "Performance test met latency objective for 96% of transactions."
        });

        engine.recordEvidence({
            "QP-003",
            100.0,
            true,
            "Release audit found no critical integrity defects."
        });

        engine.recordEvidence({
            "QP-004",
            98.0,
            false,
            "Two malformed-input security cases failed."
        });

        engine.addRisk({
            "QR-001",
            "Unexpected transaction boundaries could expose validation defects.",
            0.45,
            0.90,
            "Expand boundary-value and malformed-input testing."
        });

        engine.addRisk({
            "QR-002",
            "Peak transaction volume may increase processing latency.",
            0.30,
            0.70,
            "Execute load tests against each release candidate."
        });

        printQualityReport(engine);

        return engine.evaluateMergeEligibility() == MergeDecision::Eligible
            ? 0
            : 2;

    } catch (const std::exception& error) {
        std::cerr << "Quality planning error: "
                  << error.what() << '\n';
        return 1;
    }
}
