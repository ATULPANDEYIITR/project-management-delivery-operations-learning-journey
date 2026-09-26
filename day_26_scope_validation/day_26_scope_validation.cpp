/*
 * Scope Validation: Checking Completed Work Against Requirements
 *
 * C++17 industry-style case study.
 *
 * Scenario:
 * A software delivery team has completed several product requirements.
 * The validation system checks whether claimed completion is supported by
 * acceptance evidence, whether mandatory scope is complete, and whether
 * delivered work contains unapproved additions.
 *
 * Compile:
 *   g++ -std=c++17 -O2 scope_validation.cpp -o scope_validation
 *
 * Run:
 *   ./scope_validation
 */

#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

enum class RequirementType {
    Functional,
    NonFunctional,
    Compliance,
    Constraint
};

enum class RequirementStatus {
    NotStarted,
    InProgress,
    Complete,
    Blocked
};

enum class Severity {
    Low,
    Medium,
    High,
    Critical
};

std::string toString(RequirementType type) {
    switch (type) {
        case RequirementType::Functional:
            return "functional";
        case RequirementType::NonFunctional:
            return "non-functional";
        case RequirementType::Compliance:
            return "compliance";
        case RequirementType::Constraint:
            return "constraint";
    }

    return "unknown";
}

std::string toString(RequirementStatus status) {
    switch (status) {
        case RequirementStatus::NotStarted:
            return "not-started";
        case RequirementStatus::InProgress:
            return "in-progress";
        case RequirementStatus::Complete:
            return "complete";
        case RequirementStatus::Blocked:
            return "blocked";
    }

    return "unknown";
}

std::string toString(Severity severity) {
    switch (severity) {
        case Severity::Low:
            return "low";
        case Severity::Medium:
            return "medium";
        case Severity::High:
            return "high";
        case Severity::Critical:
            return "critical";
    }

    return "unknown";
}

// -----------------------------------------------------------------------------
// 1. DOMAIN MODEL
// -----------------------------------------------------------------------------

struct Requirement {
    std::string id;
    std::string description;
    RequirementType type;
    bool mandatory;
    std::vector<std::string> acceptanceCriteria;
    std::vector<std::string> dependencies;
    RequirementStatus status;
};

struct Evidence {
    std::string id;
    std::string requirementId;
    std::string description;
    std::string source;
    bool valid;
};

struct Finding {
    std::string requirementId;
    Severity severity;
    std::string message;
    std::vector<std::string> evidenceIds;
};

struct ValidationResult {
    bool passed;
    double coveragePercent;
    std::size_t mandatoryTotal;
    std::size_t mandatorySatisfied;
    std::vector<Finding> findings;
};

// -----------------------------------------------------------------------------
// 2. INPUT VALIDATION
// -----------------------------------------------------------------------------

void validateRequirement(const Requirement& requirement) {
    if (requirement.id.empty()) {
        throw std::invalid_argument("Requirement ID cannot be empty.");
    }

    if (requirement.description.empty()) {
        throw std::invalid_argument(
            "Requirement description cannot be empty."
        );
    }
}

void validateEvidence(const Evidence& evidence) {
    if (evidence.id.empty() ||
        evidence.requirementId.empty() ||
        evidence.description.empty() ||
        evidence.source.empty()) {
        throw std::invalid_argument(
            "Evidence must contain ID, requirement, description, and source."
        );
    }
}

// -----------------------------------------------------------------------------
// 3. EVIDENCE INDEX
// -----------------------------------------------------------------------------

class EvidenceIndex {
private:
    std::unordered_map<std::string, std::vector<const Evidence*>> index;

public:
    explicit EvidenceIndex(const std::vector<Evidence>& evidence) {
        for (const auto& item : evidence) {
            if (item.valid) {
                index[item.requirementId].push_back(&item);
            }
        }
    }

    const std::vector<const Evidence*>& forRequirement(
        const std::string& requirementId
    ) const {
        static const std::vector<const Evidence*> empty;

        auto iterator = index.find(requirementId);

        if (iterator == index.end()) {
            return empty;
        }

        return iterator->second;
    }

    std::size_t keyCount() const {
        return index.size();
    }
};

// -----------------------------------------------------------------------------
// 4. VALIDATION ENGINE
// -----------------------------------------------------------------------------

class ScopeValidator {
private:
    const std::vector<Requirement>& requirements;
    const EvidenceIndex& evidenceIndex;

    static void addFinding(
        std::vector<Finding>& findings,
        const Requirement& requirement,
        Severity severity,
        const std::string& message
    ) {
        findings.push_back({
            requirement.id,
            severity,
            message,
            {}
        });
    }

public:
    ScopeValidator(
        const std::vector<Requirement>& requirements,
        const EvidenceIndex& evidenceIndex
    )
        : requirements(requirements),
          evidenceIndex(evidenceIndex) {}

    ValidationResult validate() const {
        std::vector<Finding> findings;

        std::size_t mandatoryTotal = 0;
        std::size_t mandatorySatisfied = 0;

        for (const auto& requirement : requirements) {
            const auto& evidence =
                evidenceIndex.forRequirement(requirement.id);

            if (requirement.mandatory) {
                ++mandatoryTotal;

                if (
                    requirement.status == RequirementStatus::Complete &&
                    !evidence.empty()
                ) {
                    ++mandatorySatisfied;
                } else if (
                    requirement.status != RequirementStatus::Complete
                ) {
                    Severity severity =
                        requirement.status == RequirementStatus::Blocked
                            ? Severity::Critical
                            : Severity::High;

                    addFinding(
                        findings,
                        requirement,
                        severity,
                        "Mandatory requirement is not complete."
                    );
                } else {
                    addFinding(
                        findings,
                        requirement,
                        Severity::High,
                        "Requirement is complete but lacks valid evidence."
                    );
                }
            }

            if (
                requirement.status == RequirementStatus::Complete &&
                evidence.empty()
            ) {
                addFinding(
                    findings,
                    requirement,
                    Severity::Medium,
                    "Completion claim has no traceable evidence."
                );
            }
        }

        double coverage = mandatoryTotal == 0
            ? 100.0
            : static_cast<double>(mandatorySatisfied) /
              static_cast<double>(mandatoryTotal) * 100.0;

        bool blockingFinding = std::any_of(
            findings.begin(),
            findings.end(),
            [](const Finding& finding) {
                return finding.severity == Severity::High ||
                       finding.severity == Severity::Critical;
            }
        );

        return {
            mandatorySatisfied == mandatoryTotal && !blockingFinding,
            coverage,
            mandatoryTotal,
            mandatorySatisfied,
            findings
        };
    }
};

// -----------------------------------------------------------------------------
// 5. TRACEABILITY MATRIX
// -----------------------------------------------------------------------------

struct MatrixRow {
    std::string id;
    std::string description;
    RequirementStatus status;
    bool mandatory;
    std::size_t evidenceCount;
};

std::vector<MatrixRow> buildTraceabilityMatrix(
    const std::vector<Requirement>& requirements,
    const EvidenceIndex& evidenceIndex
) {
    std::vector<MatrixRow> matrix;

    for (const auto& requirement : requirements) {
        matrix.push_back({
            requirement.id,
            requirement.description,
            requirement.status,
            requirement.mandatory,
            evidenceIndex.forRequirement(requirement.id).size()
        });
    }

    return matrix;
}

void printMatrix(const std::vector<MatrixRow>& matrix) {
    std::cout << "\nRequirement Traceability Matrix\n";
    std::cout << std::string(110, '-') << '\n';

    for (const auto& row : matrix) {
        std::cout
            << std::left
            << std::setw(10) << row.id
            << std::setw(13) << (row.mandatory ? "mandatory" : "optional")
            << std::setw(15) << toString(row.status)
            << std::setw(12) << row.evidenceCount
            << row.description
            << '\n';
    }
}

// -----------------------------------------------------------------------------
// 6. SCOPE BOUNDARY ANALYSIS
// -----------------------------------------------------------------------------

struct ScopeAnalysis {
    std::set<std::string> deliveredInScope;
    std::set<std::string> completedOutsideScope;
    std::set<std::string> approvedButMissing;
};

ScopeAnalysis analyzeScope(
    const std::set<std::string>& approved,
    const std::set<std::string>& completed
) {
    ScopeAnalysis result;

    std::set_intersection(
        approved.begin(),
        approved.end(),
        completed.begin(),
        completed.end(),
        std::inserter(
            result.deliveredInScope,
            result.deliveredInScope.begin()
        )
    );

    std::set_difference(
        completed.begin(),
        completed.end(),
        approved.begin(),
        approved.end(),
        std::inserter(
            result.completedOutsideScope,
            result.completedOutsideScope.begin()
        )
    );

    std::set_difference(
        approved.begin(),
        approved.end(),
        completed.begin(),
        completed.end(),
        std::inserter(
            result.approvedButMissing,
            result.approvedButMissing.begin()
        )
    );

    return result;
}

void printSet(
    const std::string& name,
    const std::set<std::string>& values
) {
    std::cout << name << ": ";

    if (values.empty()) {
        std::cout << "(none)";
    } else {
        bool first = true;

        for (const auto& value : values) {
            if (!first) {
                std::cout << ", ";
            }

            std::cout << value;
            first = false;
        }
    }

    std::cout << '\n';
}

// -----------------------------------------------------------------------------
// 7. ACCEPTANCE CRITERIA
// -----------------------------------------------------------------------------

bool acceptanceCriteriaSatisfied(
    const Requirement& requirement,
    const std::set<std::string>& completedCriteria,
    std::vector<std::string>& missing
) {
    for (const auto& criterion : requirement.acceptanceCriteria) {
        if (!completedCriteria.contains(criterion)) {
            missing.push_back(criterion);
        }
    }

    return missing.empty();
}

// -----------------------------------------------------------------------------
// 8. PERFORMANCE MODEL
// -----------------------------------------------------------------------------

std::vector<Evidence> generateEvidence(std::size_t count) {
    std::vector<Evidence> evidence;
    evidence.reserve(count);

    for (std::size_t index = 0; index < count; ++index) {
        evidence.push_back({
            "EV-" + std::to_string(index),
            "REQ-" + std::to_string(index % 1000),
            "Automated validation evidence",
            "CI",
            true
        });
    }

    return evidence;
}

void performanceDemonstration() {
    constexpr std::size_t evidenceCount = 100000;

    auto evidence = generateEvidence(evidenceCount);

    auto start = std::chrono::high_resolution_clock::now();

    EvidenceIndex index(evidence);

    auto finish = std::chrono::high_resolution_clock::now();

    const auto elapsed =
        std::chrono::duration<double, std::milli>(
            finish - start
        ).count();

    std::cout << "\nPerformance demonstration\n";
    std::cout << "Evidence records: " << evidence.size() << '\n';
    std::cout << "Indexed requirement keys: "
              << index.keyCount() << '\n';
    std::cout << "Index construction time: "
              << std::fixed << std::setprecision(3)
              << elapsed << " ms\n";
}

// -----------------------------------------------------------------------------
// 9. CASE STUDY DATA
// -----------------------------------------------------------------------------

std::vector<Requirement> createRequirements() {
    return {
        {
            "REQ-001",
            "Users can authenticate.",
            RequirementType::Functional,
            true,
            {
                "valid credentials accepted",
                "invalid credentials rejected"
            },
            {},
            RequirementStatus::Complete
        },
        {
            "REQ-002",
            "Users can reset passwords.",
            RequirementType::Functional,
            true,
            {
                "reset token generated",
                "expired token rejected"
            },
            {},
            RequirementStatus::Complete
        },
        {
            "REQ-003",
            "Security events are audited.",
            RequirementType::Compliance,
            true,
            {
                "successful authentication is recorded"
            },
            {},
            RequirementStatus::Complete
        },
        {
            "REQ-004",
            "Dark mode is available.",
            RequirementType::Functional,
            false,
            {
                "dark theme renders"
            },
            {},
            RequirementStatus::Complete
        },
        {
            "REQ-005",
            "API latency meets the agreed target.",
            RequirementType::NonFunctional,
            true,
            {
                "95th percentile is below the target"
            },
            {"REQ-001"},
            RequirementStatus::InProgress
        }
    };
}

std::vector<Evidence> createEvidence() {
    return {
        {
            "EV-001",
            "REQ-001",
            "Authentication acceptance tests passed.",
            "CI pipeline",
            true
        },
        {
            "EV-002",
            "REQ-002",
            "Password reset acceptance tests passed.",
            "CI pipeline",
            true
        },
        {
            "EV-003",
            "REQ-003",
            "Audit verification passed.",
            "Compliance test",
            true
        },
        {
            "EV-004",
            "REQ-004",
            "Dark mode browser test passed.",
            "Browser test",
            true
        }
    };
}

// -----------------------------------------------------------------------------
// 10. RELEASE DECISION
// -----------------------------------------------------------------------------

std::string releaseDecision(const ValidationResult& result) {
    const bool criticalFinding = std::any_of(
        result.findings.begin(),
        result.findings.end(),
        [](const Finding& finding) {
            return finding.severity == Severity::Critical;
        }
    );

    if (criticalFinding) {
        return "BLOCKED: critical validation finding.";
    }

    if (!result.passed) {
        return "NOT READY: mandatory scope is not fully validated.";
    }

    return "VALIDATED: mandatory scope has supporting evidence.";
}

void printFindings(const std::vector<Finding>& findings) {
    std::cout << "\nValidation findings\n";

    if (findings.empty()) {
        std::cout << "No findings.\n";
        return;
    }

    for (const auto& finding : findings) {
        std::cout
            << finding.requirementId
            << " | "
            << toString(finding.severity)
            << " | "
            << finding.message
            << '\n';
    }
}

// -----------------------------------------------------------------------------
// 11. MAIN CASE STUDY
// -----------------------------------------------------------------------------

int main() {
    try {
        std::cout << std::string(90, '=') << '\n';
        std::cout << "SCOPE VALIDATION CASE STUDY\n";
        std::cout << std::string(90, '=') << '\n';

        const auto requirements = createRequirements();
        const auto evidence = createEvidence();

        for (const auto& requirement : requirements) {
            validateRequirement(requirement);
        }

        for (const auto& item : evidence) {
            validateEvidence(item);
        }

        EvidenceIndex evidenceIndex(evidence);

        ScopeValidator validator(
            requirements,
            evidenceIndex
        );

        const ValidationResult result = validator.validate();

        std::cout << "\nValidation metrics\n";
        std::cout
            << "Mandatory requirements: "
            << result.mandatoryTotal
            << '\n';

        std::cout
            << "Mandatory requirements satisfied: "
            << result.mandatorySatisfied
            << '\n';

        std::cout
            << "Mandatory evidence coverage: "
            << std::fixed
            << std::setprecision(2)
            << result.coveragePercent
            << "%\n";

        std::cout
            << "Validation passed: "
            << (result.passed ? "yes" : "no")
            << '\n';

        printFindings(result.findings);

        const auto matrix =
            buildTraceabilityMatrix(requirements, evidenceIndex);

        printMatrix(matrix);

        std::set<std::string> approvedScope = {
            "authentication",
            "password reset",
            "audit logging"
        };

        std::set<std::string> completedWork = {
            "authentication",
            "password reset",
            "audit logging",
            "dark mode",
            "CSV export"
        };

        const auto scope =
            analyzeScope(approvedScope, completedWork);

        std::cout << "\nScope boundary analysis\n";
        printSet("Delivered in scope", scope.deliveredInScope);
        printSet("Completed outside scope", scope.completedOutsideScope);
        printSet("Approved but missing", scope.approvedButMissing);

        std::set<std::string> completedCriteria = {
            "valid credentials accepted",
            "invalid credentials rejected"
        };

        std::vector<std::string> missingCriteria;

        const bool criteriaPassed =
            acceptanceCriteriaSatisfied(
                requirements.front(),
                completedCriteria,
                missingCriteria
            );

        std::cout
            << "\nAcceptance criteria for "
            << requirements.front().id
            << ": "
            << (criteriaPassed ? "passed" : "failed")
            << '\n';

        if (!criteriaPassed) {
            for (const auto& criterion : missingCriteria) {
                std::cout << "Missing: " << criterion << '\n';
            }
        }

        std::cout << "\nRelease decision\n";
        std::cout << releaseDecision(result) << '\n';

        performanceDemonstration();

        std::cout << "\nArchitectural principles demonstrated\n";
        std::cout << "1. Requirements define the validation boundary.\n";
        std::cout << "2. Completion status is different from validated completion.\n";
        std::cout << "3. Evidence provides traceability.\n";
        std::cout << "4. Mandatory scope can be used as a release gate.\n";
        std::cout << "5. Out-of-scope work must be identified separately.\n";
        std::cout << "6. Indexing avoids repeatedly scanning large evidence collections.\n";
        std::cout << "7. Validation findings should identify severity and affected requirements.\n";

        return result.passed ? 0 : 2;
    }
    catch (const std::exception& error) {
        std::cerr
            << "Validation system error: "
            << error.what()
            << '\n';

        return 1;
    }
}
