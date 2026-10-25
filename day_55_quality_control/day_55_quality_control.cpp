#include <algorithm>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

enum class Severity { Critical, Major, Minor, Observation };
enum class FindingState { Open, Fixed, Verified, Accepted };
enum class OutputState { Draft, Inspection, Rework, Released, Rejected };

std::string to_string(Severity value) {
    switch (value) {
        case Severity::Critical: return "CRITICAL";
        case Severity::Major: return "MAJOR";
        case Severity::Minor: return "MINOR";
        case Severity::Observation: return "OBSERVATION";
    }
    throw std::logic_error("Unknown severity");
}

std::string to_string(OutputState value) {
    switch (value) {
        case OutputState::Draft: return "DRAFT";
        case OutputState::Inspection: return "INSPECTION";
        case OutputState::Rework: return "REWORK";
        case OutputState::Released: return "RELEASED";
        case OutputState::Rejected: return "REJECTED";
    }
    throw std::logic_error("Unknown output state");
}

struct Requirement {
    std::string id;
    std::string description;
    bool mandatory = true;
};

struct Finding {
    std::string requirement_id;
    Severity severity;
    std::string message;
    std::string evidence;
    FindingState state = FindingState::Open;

    bool blocks_release() const {
        return state == FindingState::Open &&
               (severity == Severity::Critical || severity == Severity::Major);
    }

    void mark_fixed() {
        if (state != FindingState::Open && state != FindingState::Accepted) {
            throw std::logic_error("Finding cannot be marked fixed from this state");
        }
        state = FindingState::Fixed;
    }

    void verify() {
        if (state != FindingState::Fixed) {
            throw std::logic_error("Only fixed findings can be verified");
        }
        state = FindingState::Verified;
    }
};

struct Inspection {
    std::string inspector;
    std::vector<Finding> findings;

    bool passed() const {
        return std::none_of(findings.begin(), findings.end(),
                            [](const Finding& finding) {
                                return finding.blocks_release();
                            });
    }
};

struct AuditEvent {
    std::string action;
    std::string actor;
    std::string details;
};

class QualityEngine {
private:
    std::string output_id_;
    std::string name_;
    std::string version_;
    OutputState state_ = OutputState::Draft;
    std::map<std::string, Requirement> requirements_;
    std::vector<Inspection> inspections_;
    std::vector<AuditEvent> audit_;

    void record(std::string action, std::string actor, std::string details) {
        audit_.push_back({std::move(action), std::move(actor), std::move(details)});
    }

    bool has_unresolved_major_findings() const {
        for (const auto& inspection : inspections_) {
            for (const auto& finding : inspection.findings) {
                if (finding.blocks_release()) return true;
            }
        }
        return false;
    }

public:
    QualityEngine(std::string id, std::string name, std::string version,
                  std::vector<Requirement> requirements)
        : output_id_(std::move(id)),
          name_(std::move(name)),
          version_(std::move(version)) {
        if (output_id_.empty() || name_.empty() || version_.empty()) {
            throw std::invalid_argument("Output identity and version are required");
        }
        if (requirements.empty()) {
            throw std::invalid_argument("At least one requirement is required");
        }

        for (const auto& requirement : requirements) {
            if (requirement.id.empty() || requirement.description.empty()) {
                throw std::invalid_argument("Incomplete requirement");
            }
            if (!requirements_.emplace(requirement.id, requirement).second) {
                throw std::invalid_argument("Duplicate requirement: " + requirement.id);
            }
        }
    }

    Inspection inspect(const std::string& inspector,
                       const std::map<std::string, std::pair<bool, std::string>>& results) {
        if (state_ == OutputState::Released || state_ == OutputState::Rejected) {
            throw std::logic_error("Terminal output cannot be inspected");
        }
        if (inspector.empty()) {
            throw std::invalid_argument("Inspector identity is required");
        }

        for (const auto& result : results) {
            if (requirements_.find(result.first) == requirements_.end()) {
                throw std::invalid_argument("Unknown requirement: " + result.first);
            }
        }

        Inspection inspection;
        inspection.inspector = inspector;

        for (const auto& entry : requirements_) {
            const Requirement& requirement = entry.second;
            const auto result = results.find(requirement.id);

            if (result == results.end()) {
                if (requirement.mandatory) {
                    inspection.findings.push_back({
                        requirement.id, Severity::Major,
                        "Mandatory requirement was not checked.", ""
                    });
                }
                continue;
            }

            if (!result->second.first) {
                inspection.findings.push_back({
                    requirement.id,
                    requirement.mandatory ? Severity::Major : Severity::Minor,
                    requirement.description,
                    result->second.second
                });
            }
        }

        state_ = inspection.passed() ? OutputState::Inspection : OutputState::Rework;
        record("INSPECTION", inspector,
               "Finding count: " + std::to_string(inspection.findings.size()));
        inspections_.push_back(inspection);
        return inspection;
    }

    void release(const std::string& approver) {
        if (state_ != OutputState::Inspection || inspections_.empty() ||
            !inspections_.back().passed()) {
            throw std::logic_error("Latest inspection must pass before release");
        }
        if (has_unresolved_major_findings()) {
            throw std::logic_error("Unresolved major findings block release");
        }
        if (approver.empty()) {
            throw std::invalid_argument("Release approver is required");
        }

        state_ = OutputState::Released;
        record("RELEASE", approver, "Version " + version_);
    }

    void reject(const std::string& actor, const std::string& reason) {
        if (state_ == OutputState::Released) {
            throw std::logic_error("Released output cannot be rejected retroactively");
        }
        if (actor.empty() || reason.empty()) {
            throw std::invalid_argument("Actor and rejection reason are required");
        }
        state_ = OutputState::Rejected;
        record("REJECTION", actor, reason);
    }

    void print_report() const {
        std::cout << "\nQuality Report: " << name_ << '\n'
                  << "Output ID: " << output_id_ << '\n'
                  << "Version: " << version_ << '\n'
                  << "Status: " << to_string(state_) << '\n'
                  << "Inspection count: " << inspections_.size() << '\n';

        for (std::size_t i = 0; i < inspections_.size(); ++i) {
            const auto& inspection = inspections_[i];
            std::cout << "\nInspection " << i + 1
                      << " by " << inspection.inspector
                      << ": " << (inspection.passed() ? "PASS" : "FAIL") << '\n';

            for (const auto& finding : inspection.findings) {
                std::cout << "  [" << to_string(finding.severity) << "] "
                          << finding.requirement_id << ": "
                          << finding.message;
                if (!finding.evidence.empty()) {
                    std::cout << " | Evidence: " << finding.evidence;
                }
                std::cout << '\n';
            }
        }

        std::cout << "\nAudit events: " << audit_.size() << '\n';
        for (const auto& event : audit_) {
            std::cout << "  " << event.action << " by " << event.actor
                      << " | " << event.details << '\n';
        }
    }
};

int main() {
    try {
        QualityEngine engine(
            "OUT-2026-041",
            "Monthly Production Dashboard",
            "3.4",
            {
                {"Q1", "Required production metrics are present", true},
                {"Q2", "Totals reconcile with source records", true},
                {"Q3", "Colors and labels follow the style guide", false},
                {"Q4", "Export file opens successfully", true}
            }
        );

        const Inspection inspection = engine.inspect(
            "quality-engineer",
            {
                {"Q1", {true, "Metric inventory checked"}},
                {"Q2", {false, "Dashboard total 15040; source total 14980"}},
                {"Q3", {true, "Style guide checked"}},
                {"Q4", {true, "CSV export parsed successfully"}}
            }
        );

        std::cout << "Initial inspection: "
                  << (inspection.passed() ? "PASS" : "FAIL") << '\n';

        try {
            engine.release("operations-manager");
        } catch (const std::logic_error& error) {
            std::cout << "Release denied: " << error.what() << '\n';
        }

        engine.print_report();

        // A small independent check verifies that absent mandatory evidence fails.
        QualityEngine edge_case(
            "OUT-EDGE",
            "Incomplete Inspection",
            "1.0",
            {{"REQ-1", "Source records reconciled", true}}
        );
        const auto missing = edge_case.inspect("reviewer", {});
        if (missing.passed()) {
            throw std::runtime_error("Missing mandatory evidence was not detected");
        }
        std::cout << "\nMissing-evidence validation passed.\n";
    } catch (const std::exception& error) {
        std::cerr << "Quality control error: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
