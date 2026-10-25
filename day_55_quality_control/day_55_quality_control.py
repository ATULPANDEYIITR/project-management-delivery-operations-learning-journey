#!/usr/bin/env python3
"""Quality control system for checking project outputs."""

from __future__ import annotations

import json
import re
import unittest
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4


class Severity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    OBSERVATION = "observation"


class FindingStatus(str, Enum):
    OPEN = "open"
    ACCEPTED = "accepted"
    FIXED = "fixed"
    VERIFIED = "verified"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    INSPECTION = "inspection"
    REWORK = "rework"
    RELEASED = "released"
    REJECTED = "rejected"


@dataclass(frozen=True)
class QualityRequirement:
    requirement_id: str
    description: str
    mandatory: bool = True


@dataclass
class Finding:
    finding_id: str
    requirement_id: str
    severity: Severity
    description: str
    status: FindingStatus = FindingStatus.OPEN
    evidence: str = ""
    assigned_to: str = ""

    def resolve(self, verified: bool = False) -> None:
        if self.status not in (FindingStatus.OPEN, FindingStatus.ACCEPTED,
                               FindingStatus.FIXED):
            raise ValueError("Finding cannot transition from its current state.")
        self.status = (
            FindingStatus.VERIFIED if verified else FindingStatus.FIXED
        )


@dataclass
class Inspection:
    inspection_id: str
    inspector: str
    inspected_at: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(
            finding.status == FindingStatus.OPEN
            and finding.severity in (Severity.CRITICAL, Severity.MAJOR)
            for finding in self.findings
        )


@dataclass
class ProjectOutput:
    output_id: str
    name: str
    version: str
    artifact_path: str
    requirements: list[QualityRequirement]
    status: ProjectStatus = ProjectStatus.DRAFT
    inspections: list[Inspection] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)

    def record(self, action: str, actor: str, details: str = "") -> None:
        self.history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "actor": actor,
            "details": details,
        })

    def inspect(self, inspector: str, results: dict[str, tuple[bool, str]]) -> Inspection:
        if self.status in (ProjectStatus.RELEASED, ProjectStatus.REJECTED):
            raise ValueError("Terminal outputs cannot be inspected again.")

        known = {r.requirement_id for r in self.requirements}
        unknown = set(results) - known
        if unknown:
            raise ValueError(f"Unknown requirements: {sorted(unknown)}")

        findings: list[Finding] = []
        for requirement in self.requirements:
            result = results.get(requirement.requirement_id)
            if result is None:
                if requirement.mandatory:
                    findings.append(Finding(
                        str(uuid4()), requirement.requirement_id,
                        Severity.MAJOR, "Mandatory requirement was not checked."
                    ))
                continue

            passed, evidence = result
            if not passed:
                findings.append(Finding(
                    str(uuid4()),
                    requirement.requirement_id,
                    Severity.MAJOR if requirement.mandatory else Severity.MINOR,
                    f"Requirement failed: {requirement.description}",
                    evidence=evidence,
                ))

        inspection = Inspection(
            str(uuid4()), inspector,
            datetime.now(timezone.utc).isoformat(), findings
        )
        self.inspections.append(inspection)
        self.status = (
            ProjectStatus.INSPECTION if inspection.passed
            else ProjectStatus.REWORK
        )
        self.record("inspection", inspector, f"Findings: {len(findings)}")
        return inspection

    def release(self, approver: str) -> None:
        if not self.inspections:
            raise ValueError("An output must be inspected before release.")
        latest = self.inspections[-1]
        if self.status != ProjectStatus.INSPECTION or not latest.passed:
            raise ValueError("Release blocked: latest inspection did not pass.")
        if any(
            finding.status == FindingStatus.OPEN
            and finding.severity in (Severity.CRITICAL, Severity.MAJOR)
            for inspection in self.inspections
            for finding in inspection.findings
        ):
            raise ValueError("Release blocked by unresolved major findings.")
        self.status = ProjectStatus.RELEASED
        self.record("release", approver, f"Version {self.version}")

    def reject(self, actor: str, reason: str) -> None:
        if not reason.strip():
            raise ValueError("A rejection reason is required.")
        if self.status == ProjectStatus.RELEASED:
            raise ValueError("A released output cannot be rejected retroactively.")
        self.status = ProjectStatus.REJECTED
        self.record("rejection", actor, reason)


def load_requirements(path: Path) -> list[QualityRequirement]:
    """Load a JSON array of requirements and validate its structure."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot load requirements: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError("Requirements document must contain a JSON array.")

    requirements = []
    seen: set[str] = set()
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Each requirement must be an object.")
        requirement_id = str(item.get("requirement_id", "")).strip()
        description = str(item.get("description", "")).strip()
        if not requirement_id or not description:
            raise ValueError("Requirement ID and description are required.")
        if requirement_id in seen:
            raise ValueError(f"Duplicate requirement ID: {requirement_id}")
        seen.add(requirement_id)
        requirements.append(QualityRequirement(
            requirement_id,
            description,
            bool(item.get("mandatory", True)),
        ))
    return requirements


def safe_artifact_name(name: str) -> str:
    """Reject unsafe artifact names before using them in filesystem workflows."""
    if not name or name in {".", ".."}:
        raise ValueError("Invalid artifact name.")
    if Path(name).name != name or re.search(r"[/\\\x00]", name):
        raise ValueError("Artifact name must not contain a path.")
    return name


def write_report(output: ProjectOutput, destination: Path) -> None:
    """Write a local audit report; the caller controls destination permissions."""
    report = {
        "output_id": output.output_id,
        "name": output.name,
        "version": output.version,
        "status": output.status.value,
        "requirements": [asdict(r) for r in output.requirements],
        "inspections": [
            {
                "inspection_id": i.inspection_id,
                "inspector": i.inspector,
                "inspected_at": i.inspected_at,
                "passed": i.passed,
                "findings": [
                    {
                        **asdict(f),
                        "severity": f.severity.value,
                        "status": f.status.value,
                    }
                    for f in i.findings
                ],
            }
            for i in output.inspections
        ],
        "history": output.history,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    try:
        temporary.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()


class QualityControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.output = ProjectOutput(
            "OUT-101",
            "Monthly Operations Report",
            "1.0",
            "monthly-report.pdf",
            [
                QualityRequirement("Q1", "All required sections are present"),
                QualityRequirement("Q2", "Totals reconcile with source data"),
                QualityRequirement("Q3", "Formatting is consistent", False),
            ],
        )

    def test_successful_inspection_and_release(self) -> None:
        inspection = self.output.inspect("reviewer-1", {
            "Q1": (True, "Section checklist"),
            "Q2": (True, "Reconciliation worksheet"),
            "Q3": (True, "Style checklist"),
        })
        self.assertTrue(inspection.passed)
        self.output.release("quality-manager")
        self.assertEqual(self.output.status, ProjectStatus.RELEASED)

    def test_failed_mandatory_requirement_blocks_release(self) -> None:
        self.output.inspect("reviewer-1", {
            "Q1": (True, "Checklist"),
            "Q2": (False, "Total differs by 125"),
            "Q3": (True, "Style checklist"),
        })
        with self.assertRaises(ValueError):
            self.output.release("quality-manager")

    def test_missing_requirement_is_detected(self) -> None:
        inspection = self.output.inspect("reviewer-1", {"Q1": (True, "Checked")})
        self.assertFalse(inspection.passed)
        self.assertEqual(len(inspection.findings), 2)

    def test_unknown_requirement_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.output.inspect("reviewer-1", {"Q999": (True, "Invalid")})

    def test_path_traversal_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            safe_artifact_name("../report.pdf")


def main() -> None:
    requirements = [
        QualityRequirement("Q1", "Required sections are complete"),
        QualityRequirement("Q2", "Figures reconcile to source records"),
        QualityRequirement("Q3", "File opens and is readable"),
        QualityRequirement("Q4", "Naming convention is followed", False),
    ]

    output = ProjectOutput(
        "OUT-2026-001",
        "Quarterly Performance Report",
        "2.1",
        safe_artifact_name("quarterly-performance.pdf"),
        requirements,
    )

    inspection = output.inspect("quality-reviewer", {
        "Q1": (True, "Sections checklist completed"),
        "Q2": (False, "Reported total 128400; source total 128250"),
        "Q3": (True, "PDF opened successfully"),
        "Q4": (True, "Filename checked"),
    })

    print(f"Output: {output.name} v{output.version}")
    print(f"Inspection passed: {inspection.passed}")
    for finding in inspection.findings:
        print(f"{finding.severity.value.upper()}: {finding.description}")

    if output.status == ProjectStatus.INSPECTION:
        output.release("quality-manager")
    else:
        print("Release blocked; correct the findings and reinspect.")

    print(f"Current status: {output.status.value}")
    print(f"Audit events: {len(output.history)}")


if __name__ == "__main__":
    main()
