"""
Scope Validation: Checking Completed Work Against Requirements

A self-contained study program covering scope validation from beginner to
advanced level through executable examples.

The program models requirements, completed work, validation rules, evidence,
defects, traceability, coverage, exceptions, risk, and release decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable
import json
import time


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL TERMINOLOGY
# ---------------------------------------------------------------------------

class RequirementType(Enum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non-functional"
    COMPLIANCE = "compliance"
    CONSTRAINT = "constraint"


class RequirementStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    BLOCKED = "blocked"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Requirement:
    requirement_id: str
    description: str
    requirement_type: RequirementType = RequirementType.FUNCTIONAL
    mandatory: bool = True
    acceptance_criteria: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    status: RequirementStatus = RequirementStatus.NOT_STARTED


@dataclass
class Evidence:
    evidence_id: str
    requirement_id: str
    description: str
    source: str
    valid: bool = True


@dataclass
class Finding:
    requirement_id: str
    severity: Severity
    message: str
    evidence_ids: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    passed: bool
    findings: list[Finding]
    coverage_percent: float
    mandatory_requirements: int
    satisfied_mandatory_requirements: int
    evaluated_requirements: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "coverage_percent": round(self.coverage_percent, 2),
            "mandatory_requirements": self.mandatory_requirements,
            "satisfied_mandatory_requirements": self.satisfied_mandatory_requirements,
            "evaluated_requirements": self.evaluated_requirements,
            "findings": [
                {
                    "requirement_id": finding.requirement_id,
                    "severity": finding.severity.value,
                    "message": finding.message,
                    "evidence_ids": finding.evidence_ids,
                }
                for finding in self.findings
            ],
        }


# ---------------------------------------------------------------------------
# 2. SIMPLE REQUIREMENT CHECKING
# ---------------------------------------------------------------------------

def is_complete(status: RequirementStatus) -> bool:
    """A requirement is complete only when its status explicitly says complete."""
    return status == RequirementStatus.COMPLETE


def validate_basic_status(requirements: Iterable[Requirement]) -> list[str]:
    """Return IDs of mandatory requirements that are not complete."""
    failures = []

    for requirement in requirements:
        if requirement.mandatory and not is_complete(requirement.status):
            failures.append(requirement.requirement_id)

    return failures


def demonstrate_basic_validation() -> None:
    requirements = [
        Requirement(
            "REQ-001",
            "Users can create an account.",
            status=RequirementStatus.COMPLETE,
        ),
        Requirement(
            "REQ-002",
            "Users can reset their password.",
            status=RequirementStatus.IN_PROGRESS,
        ),
        Requirement(
            "REQ-003",
            "System records audit events.",
            requirement_type=RequirementType.COMPLIANCE,
            status=RequirementStatus.COMPLETE,
        ),
    ]

    failures = validate_basic_status(requirements)

    print("Basic validation")
    print("Incomplete mandatory requirements:", failures)
    print()


# ---------------------------------------------------------------------------
# 3. ACCEPTANCE CRITERIA
# ---------------------------------------------------------------------------

def validate_acceptance_criteria(
    requirement: Requirement,
    completed_criteria: set[str],
) -> tuple[bool, list[str]]:
    """
    A requirement can have status COMPLETE but still fail scope validation if
    one or more acceptance criteria have not actually been demonstrated.
    """
    missing = [
        criterion
        for criterion in requirement.acceptance_criteria
        if criterion not in completed_criteria
    ]

    return len(missing) == 0, missing


def demonstrate_acceptance_criteria() -> None:
    requirement = Requirement(
        "REQ-010",
        "Export customer data.",
        acceptance_criteria=[
            "CSV export works",
            "UTF-8 encoding is preserved",
            "Unauthorized users are rejected",
        ],
        status=RequirementStatus.COMPLETE,
    )

    completed = {
        "CSV export works",
        "UTF-8 encoding is preserved",
    }

    passed, missing = validate_acceptance_criteria(requirement, completed)

    print("Acceptance criteria")
    print("Passed:", passed)
    print("Missing:", missing)
    print()


# ---------------------------------------------------------------------------
# 4. EVIDENCE AND TRACEABILITY
# ---------------------------------------------------------------------------

class ScopeValidator:
    """
    Central validator.

    Important principle:
    completion claims are not treated as proof. Evidence must be connected
    to requirements through traceability.
    """

    def __init__(
        self,
        requirements: Iterable[Requirement],
        evidence: Iterable[Evidence],
    ):
        self.requirements = list(requirements)
        self.evidence = list(evidence)

    def evidence_for(self, requirement_id: str) -> list[Evidence]:
        return [
            item
            for item in self.evidence
            if item.requirement_id == requirement_id and item.valid
        ]

    def validate(self) -> ValidationResult:
        findings: list[Finding] = []
        satisfied_mandatory = 0
        evaluated = 0

        for requirement in self.requirements:
            evidence = self.evidence_for(requirement.requirement_id)

            if requirement.status == RequirementStatus.COMPLETE:
                evaluated += 1

            if requirement.mandatory:
                if (
                    requirement.status == RequirementStatus.COMPLETE
                    and evidence
                ):
                    satisfied_mandatory += 1
                else:
                    if requirement.status != RequirementStatus.COMPLETE:
                        findings.append(
                            Finding(
                                requirement.requirement_id,
                                Severity.HIGH,
                                "Mandatory requirement is not complete.",
                            )
                        )
                    elif not evidence:
                        findings.append(
                            Finding(
                                requirement.requirement_id,
                                Severity.HIGH,
                                "Requirement is marked complete but has no valid evidence.",
                            )
                        )

            if requirement.status == RequirementStatus.COMPLETE and not evidence:
                findings.append(
                    Finding(
                        requirement.requirement_id,
                        Severity.MEDIUM,
                        "Completion claim lacks traceable evidence.",
                    )
                )

        mandatory_count = sum(
            1 for requirement in self.requirements if requirement.mandatory
        )

        coverage = (
            (satisfied_mandatory / mandatory_count * 100)
            if mandatory_count
            else 100.0
        )

        critical_or_high = any(
            finding.severity in {Severity.CRITICAL, Severity.HIGH}
            for finding in findings
        )

        return ValidationResult(
            passed=(not critical_or_high and satisfied_mandatory == mandatory_count),
            findings=findings,
            coverage_percent=coverage,
            mandatory_requirements=mandatory_count,
            satisfied_mandatory_requirements=satisfied_mandatory,
            evaluated_requirements=evaluated,
        )


# ---------------------------------------------------------------------------
# 5. REQUIREMENT MATRIX
# ---------------------------------------------------------------------------

@dataclass
class RequirementMatrix:
    requirements: list[Requirement]
    evidence: list[Evidence]

    def rows(self) -> list[dict[str, Any]]:
        rows = []

        for requirement in self.requirements:
            evidence = [
                item
                for item in self.evidence
                if item.requirement_id == requirement.requirement_id
            ]

            rows.append(
                {
                    "id": requirement.requirement_id,
                    "description": requirement.description,
                    "type": requirement.requirement_type.value,
                    "mandatory": requirement.mandatory,
                    "status": requirement.status.value,
                    "evidence_count": len(evidence),
                    "traceable": bool(evidence),
                }
            )

        return rows

    def print_table(self) -> None:
        print("Requirement traceability matrix")
        print("-" * 100)
        print(
            f"{'ID':<10} {'Mandatory':<10} {'Status':<12} "
            f"{'Evidence':<10} {'Traceable':<10} Description"
        )
        print("-" * 100)

        for row in self.rows():
            print(
                f"{row['id']:<10} "
                f"{str(row['mandatory']):<10} "
                f"{row['status']:<12} "
                f"{row['evidence_count']:<10} "
                f"{str(row['traceable']):<10} "
                f"{row['description']}"
            )

        print()


# ---------------------------------------------------------------------------
# 6. VALIDATION RULES
# ---------------------------------------------------------------------------

ValidatorFunction = Callable[[Requirement, list[Evidence]], Finding | None]


def require_evidence(
    requirement: Requirement,
    evidence: list[Evidence],
) -> Finding | None:
    if requirement.mandatory and requirement.status == RequirementStatus.COMPLETE:
        if not evidence:
            return Finding(
                requirement.requirement_id,
                Severity.HIGH,
                "Mandatory completed item has no evidence.",
            )
    return None


def reject_blocked_requirement(
    requirement: Requirement,
    evidence: list[Evidence],
) -> Finding | None:
    if requirement.status == RequirementStatus.BLOCKED:
        return Finding(
            requirement.requirement_id,
            Severity.CRITICAL if requirement.mandatory else Severity.MEDIUM,
            "Requirement is blocked.",
        )
    return None


def check_dependency_status(
    requirement: Requirement,
    evidence: list[Evidence],
) -> Finding | None:
    # Dependency resolution belongs to the project repository in a real system.
    # This rule illustrates that validation may operate on more than status.
    if requirement.dependencies and not evidence:
        return Finding(
            requirement.requirement_id,
            Severity.MEDIUM,
            "Requirement has dependencies but no supporting validation evidence.",
        )
    return None


class RuleBasedValidator:
    def __init__(self, rules: Iterable[ValidatorFunction]):
        self.rules = list(rules)

    def run(
        self,
        requirements: Iterable[Requirement],
        evidence: Iterable[Evidence],
    ) -> list[Finding]:
        evidence_list = list(evidence)
        findings = []

        for requirement in requirements:
            matching = [
                item
                for item in evidence_list
                if item.requirement_id == requirement.requirement_id
                and item.valid
            ]

            for rule in self.rules:
                finding = rule(requirement, matching)
                if finding:
                    findings.append(finding)

        return findings


# ---------------------------------------------------------------------------
# 7. EDGE CASES
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    cases = [
        Requirement(
            "EDGE-001",
            "Optional documentation.",
            mandatory=False,
            status=RequirementStatus.NOT_STARTED,
        ),
        Requirement(
            "EDGE-002",
            "Mandatory feature blocked by dependency.",
            mandatory=True,
            status=RequirementStatus.BLOCKED,
        ),
        Requirement(
            "EDGE-003",
            "Feature marked complete but without evidence.",
            mandatory=True,
            status=RequirementStatus.COMPLETE,
        ),
        Requirement(
            "EDGE-004",
            "Fully validated feature.",
            mandatory=True,
            status=RequirementStatus.COMPLETE,
        ),
    ]

    evidence = [
        Evidence(
            "EV-004",
            "EDGE-004",
            "Automated acceptance test passed.",
            "test-suite",
        )
    ]

    validator = ScopeValidator(cases, evidence)
    result = validator.validate()

    print("Edge cases")
    print(json.dumps(result.to_dict(), indent=2))
    print()


# ---------------------------------------------------------------------------
# 8. COVERAGE METRICS
# ---------------------------------------------------------------------------

def calculate_metrics(
    requirements: list[Requirement],
    evidence: list[Evidence],
) -> dict[str, float]:
    total = len(requirements)
    completed = sum(
        requirement.status == RequirementStatus.COMPLETE
        for requirement in requirements
    )

    traceable = sum(
        any(
            item.requirement_id == requirement.requirement_id and item.valid
            for item in evidence
        )
        for requirement in requirements
    )

    mandatory = [item for item in requirements if item.mandatory]
    mandatory_complete = sum(
        item.status == RequirementStatus.COMPLETE for item in mandatory
    )

    return {
        "completion_rate": (completed / total * 100) if total else 100.0,
        "traceability_rate": (traceable / total * 100) if total else 100.0,
        "mandatory_completion_rate": (
            mandatory_complete / len(mandatory) * 100
            if mandatory
            else 100.0
        ),
    }


# ---------------------------------------------------------------------------
# 9. SCOPE CREEP DETECTION
# ---------------------------------------------------------------------------

def detect_unapproved_work(
    completed_work: set[str],
    approved_scope: set[str],
) -> dict[str, set[str]]:
    """
    Work outside the approved scope is not automatically bad.

    It is flagged because it requires an explicit scope decision. This
    distinction prevents useful extra work from being silently treated as
    approved scope.
    """
    delivered = completed_work & approved_scope
    extra = completed_work - approved_scope
    missing = approved_scope - completed_work

    return {
        "delivered_in_scope": delivered,
        "completed_outside_scope": extra,
        "approved_but_missing": missing,
    }


def demonstrate_scope_creep() -> None:
    approved = {
        "login",
        "password_reset",
        "audit_log",
    }

    completed = {
        "login",
        "password_reset",
        "audit_log",
        "dark_mode",
        "csv_export",
    }

    result = detect_unapproved_work(completed, approved)

    print("Scope boundary analysis")
    for name, values in result.items():
        print(f"{name}: {sorted(values)}")
    print()


# ---------------------------------------------------------------------------
# 10. DIFFERENCE BETWEEN COMPLETION AND VALIDATION
# ---------------------------------------------------------------------------

def completion_vs_validation() -> None:
    requirement = Requirement(
        "REQ-COMPARE",
        "Generate monthly report.",
        status=RequirementStatus.COMPLETE,
    )

    evidence = []

    print("Completion vs validation")
    print("Claimed status:", requirement.status.value)
    print("Evidence count:", len(evidence))
    print(
        "Validated:",
        requirement.status == RequirementStatus.COMPLETE and bool(evidence),
    )
    print()


# ---------------------------------------------------------------------------
# 11. SECURITY AND QUALITY CONSIDERATIONS
# ---------------------------------------------------------------------------

def validate_evidence_integrity(evidence: Evidence) -> bool:
    """
    In production, evidence should also be checked for authenticity,
    authorization, timestamps, immutable storage, and provenance.
    """
    return bool(
        evidence.evidence_id.strip()
        and evidence.requirement_id.strip()
        and evidence.description.strip()
        and evidence.source.strip()
        and evidence.valid
    )


def demonstrate_evidence_security() -> None:
    evidence = Evidence(
        "EV-SEC-001",
        "REQ-SEC-001",
        "Security test report passed.",
        "CI pipeline",
    )

    print("Evidence integrity check:", validate_evidence_integrity(evidence))
    print()


# ---------------------------------------------------------------------------
# 12. PERFORMANCE CONSIDERATIONS
# ---------------------------------------------------------------------------

def indexed_evidence_map(evidence: Iterable[Evidence]) -> dict[str, list[Evidence]]:
    """
    Naive validation repeatedly scans evidence and can approach O(R * E).

    Indexing evidence by requirement reduces lookup work and is preferable
    when validating thousands of requirements and evidence records.
    """
    index: dict[str, list[Evidence]] = {}

    for item in evidence:
        index.setdefault(item.requirement_id, []).append(item)

    return index


def performance_demo() -> None:
    evidence = [
        Evidence(
            f"EV-{index}",
            f"REQ-{index % 100}",
            "Test evidence",
            "automated-test",
        )
        for index in range(10_000)
    ]

    start = time.perf_counter()
    index = indexed_evidence_map(evidence)
    elapsed = time.perf_counter() - start

    print("Performance-oriented evidence indexing")
    print("Evidence records:", len(evidence))
    print("Indexed requirements:", len(index))
    print(f"Index construction time: {elapsed:.6f} seconds")
    print()


# ---------------------------------------------------------------------------
# 13. COMPLETE CASE STUDY
# ---------------------------------------------------------------------------

def build_case_study() -> tuple[list[Requirement], list[Evidence]]:
    requirements = [
        Requirement(
            "REQ-001",
            "User authentication must work.",
            RequirementType.FUNCTIONAL,
            True,
            ["valid credentials accepted", "invalid credentials rejected"],
            status=RequirementStatus.COMPLETE,
        ),
        Requirement(
            "REQ-002",
            "Password reset must work.",
            RequirementType.FUNCTIONAL,
            True,
            ["reset token generated", "expired token rejected"],
            status=RequirementStatus.COMPLETE,
        ),
        Requirement(
            "REQ-003",
            "Audit events must be retained.",
            RequirementType.COMPLIANCE,
            True,
            ["successful login logged"],
            status=RequirementStatus.COMPLETE,
        ),
        Requirement(
            "REQ-004",
            "Optional dark mode.",
            RequirementType.FUNCTIONAL,
            False,
            ["dark theme renders"],
            status=RequirementStatus.COMPLETE,
        ),
        Requirement(
            "REQ-005",
            "API response must meet latency target.",
            RequirementType.NON_FUNCTIONAL,
            True,
            ["95th percentile below target"],
            status=RequirementStatus.IN_PROGRESS,
        ),
    ]

    evidence = [
        Evidence(
            "EV-001",
            "REQ-001",
            "Authentication integration tests passed.",
            "CI",
        ),
        Evidence(
            "EV-002",
            "REQ-002",
            "Password reset acceptance tests passed.",
            "CI",
        ),
        Evidence(
            "EV-003",
            "REQ-003",
            "Audit retention verification completed.",
            "compliance-test",
        ),
        Evidence(
            "EV-004",
            "REQ-004",
            "Browser test confirms dark mode.",
            "browser-test",
        ),
    ]

    return requirements, evidence


def run_complete_case_study() -> None:
    requirements, evidence = build_case_study()

    matrix = RequirementMatrix(requirements, evidence)
    matrix.print_table()

    validator = ScopeValidator(requirements, evidence)
    result = validator.validate()

    print("Validation result")
    print(json.dumps(result.to_dict(), indent=2))

    print("\nMetrics")
    print(json.dumps(calculate_metrics(requirements, evidence), indent=2))

    print()


# ---------------------------------------------------------------------------
# 14. PRACTICAL DECISION MODEL
# ---------------------------------------------------------------------------

def release_decision(result: ValidationResult) -> str:
    """
    This function deliberately separates mechanical validation from human
    governance. A real release process can impose additional organizational
    gates such as legal approval, risk acceptance, or management authorization.
    """
    if any(
        finding.severity == Severity.CRITICAL
        for finding in result.findings
    ):
        return "BLOCKED: critical validation finding."

    if not result.passed:
        return "NOT READY: mandatory scope requirements are not fully validated."

    return "VALIDATED: mandatory scope requirements have supporting evidence."


# ---------------------------------------------------------------------------
# 15. MAIN DEMONSTRATION
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 90)
    print("SCOPE VALIDATION STUDY PROGRAM")
    print("=" * 90)
    print()

    demonstrate_basic_validation()
    demonstrate_acceptance_criteria()
    demonstrate_edge_cases()
    demonstrate_scope_creep()
    completion_vs_validation()
    demonstrate_evidence_security()
    performance_demo()

    requirements, evidence = build_case_study()
    result = ScopeValidator(requirements, evidence).validate()

    print("Release decision")
    print(release_decision(result))
    print()

    print("=" * 90)
    print("COMPLETE CASE STUDY")
    print("=" * 90)
    run_complete_case_study()

    print("Core principles demonstrated:")
    principles = [
        "Scope is validated against explicit requirements, not memory.",
        "Completion status is a claim; evidence establishes traceability.",
        "Mandatory and optional requirements must be treated differently.",
        "Acceptance criteria provide a finer validation boundary.",
        "Out-of-scope work requires an explicit scope decision.",
        "Validation findings should have severity and evidence.",
        "Large validation systems benefit from indexed traceability data.",
        "Validation should be reproducible, auditable, and deterministic.",
    ]

    for number, principle in enumerate(principles, start=1):
        print(f"{number}. {principle}")


if __name__ == "__main__":
    main()
