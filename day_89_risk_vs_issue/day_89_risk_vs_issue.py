from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4
import json


class RiskStatus(Enum):
    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    MITIGATING = "mitigating"
    ACCEPTED = "accepted"
    CLOSED = "closed"


class IssueStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Severity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Risk:
    title: str
    description: str
    probability: int
    impact: int
    owner: str
    category: str = "Operational"
    mitigation: str = ""
    contingency: str = ""
    status: RiskStatus = RiskStatus.IDENTIFIED
    risk_id: str = field(default_factory=lambda: str(uuid4()))
    identified_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self):
        if not self.title.strip():
            raise ValueError("Risk title cannot be empty.")
        if not 1 <= self.probability <= 5:
            raise ValueError("Probability must be between 1 and 5.")
        if not 1 <= self.impact <= 5:
            raise ValueError("Impact must be between 1 and 5.")
        if not self.owner.strip():
            raise ValueError("Risk owner is required.")

    @property
    def exposure(self) -> int:
        return self.probability * self.impact

    @property
    def severity(self) -> Severity:
        if self.exposure >= 20:
            return Severity.CRITICAL
        if self.exposure >= 12:
            return Severity.HIGH
        if self.exposure >= 6:
            return Severity.MEDIUM
        return Severity.LOW

    def assess(self):
        if self.status == RiskStatus.CLOSED:
            raise ValueError("A closed risk cannot be reassessed.")
        self.status = RiskStatus.ASSESSED

    def start_mitigation(self):
        if self.status not in (
            RiskStatus.IDENTIFIED,
            RiskStatus.ASSESSED
        ):
            raise ValueError("Invalid risk mitigation transition.")
        if not self.mitigation.strip():
            raise ValueError("A mitigation plan is required.")
        self.status = RiskStatus.MITIGATING

    def accept(self):
        if self.status == RiskStatus.CLOSED:
            raise ValueError("Closed risk cannot be accepted.")
        self.status = RiskStatus.ACCEPTED

    def close(self):
        if self.status not in (
            RiskStatus.MITIGATING,
            RiskStatus.ACCEPTED
        ):
            raise ValueError("Risk must be mitigated or accepted before closure.")
        self.status = RiskStatus.CLOSED


@dataclass
class Issue:
    title: str
    description: str
    severity: Severity
    priority: Priority
    owner: str
    source_risk_id: Optional[str] = None
    status: IssueStatus = IssueStatus.OPEN
    issue_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    resolution: str = ""

    def __post_init__(self):
        if not self.title.strip():
            raise ValueError("Issue title cannot be empty.")
        if not self.description.strip():
            raise ValueError("Issue description cannot be empty.")
        if not self.owner.strip():
            raise ValueError("Issue owner is required.")

    def start(self):
        if self.status != IssueStatus.OPEN:
            raise ValueError("Only open issues can be started.")
        self.status = IssueStatus.IN_PROGRESS

    def block(self):
        if self.status not in (
            IssueStatus.OPEN,
            IssueStatus.IN_PROGRESS
        ):
            raise ValueError("Issue cannot enter blocked state.")
        self.status = IssueStatus.BLOCKED

    def resolve(self, resolution: str):
        if self.status not in (
            IssueStatus.OPEN,
            IssueStatus.IN_PROGRESS,
            IssueStatus.BLOCKED
        ):
            raise ValueError("Issue cannot be resolved from current state.")
        if not resolution.strip():
            raise ValueError("Resolution details are required.")
        self.resolution = resolution
        self.status = IssueStatus.RESOLVED

    def close(self):
        if self.status != IssueStatus.RESOLVED:
            raise ValueError("Only resolved issues can be closed.")
        self.status = IssueStatus.CLOSED


class RiskIssueManager:
    """
    Maintains separate risk and issue registers.

    Risks represent uncertain future events.
    Issues represent events or conditions that already exist.
    """

    def __init__(self):
        self.risks: dict[str, Risk] = {}
        self.issues: dict[str, Issue] = {}

    def add_risk(self, risk: Risk):
        if risk.risk_id in self.risks:
            raise ValueError("Duplicate risk identifier.")
        self.risks[risk.risk_id] = risk

    def add_issue(self, issue: Issue):
        if issue.issue_id in self.issues:
            raise ValueError("Duplicate issue identifier.")

        if issue.source_risk_id is not None:
            if issue.source_risk_id not in self.risks:
                raise ValueError("Source risk does not exist.")

        self.issues[issue.issue_id] = issue

    def convert_risk_to_issue(
        self,
        risk_id: str,
        issue_title: str,
        issue_description: str,
        owner: Optional[str] = None
    ) -> Issue:
        """
        Creates an issue when a previously identified risk materializes.

        The original risk remains in the risk register for traceability.
        """
        risk = self.risks.get(risk_id)

        if risk is None:
            raise KeyError("Risk not found.")

        issue = Issue(
            title=issue_title,
            description=issue_description,
            severity=risk.severity,
            priority=self._priority_from_severity(risk.severity),
            owner=owner or risk.owner,
            source_risk_id=risk_id
        )

        self.add_issue(issue)
        return issue

    @staticmethod
    def _priority_from_severity(severity: Severity) -> Priority:
        mapping = {
            Severity.LOW: Priority.LOW,
            Severity.MEDIUM: Priority.MEDIUM,
            Severity.HIGH: Priority.HIGH,
            Severity.CRITICAL: Priority.URGENT
        }
        return mapping[severity]

    def highest_risks(self, limit: int = 5) -> list[Risk]:
        if limit < 1:
            raise ValueError("Limit must be positive.")

        return sorted(
            (
                risk for risk in self.risks.values()
                if risk.status != RiskStatus.CLOSED
            ),
            key=lambda risk: (
                risk.exposure,
                risk.impact,
                risk.probability
            ),
            reverse=True
        )[:limit]

    def unresolved_issues(self) -> list[Issue]:
        return [
            issue for issue in self.issues.values()
            if issue.status not in (
                IssueStatus.RESOLVED,
                IssueStatus.CLOSED
            )
        ]

    def dashboard(self) -> dict:
        risk_counts = {
            status.value: sum(
                risk.status == status
                for risk in self.risks.values()
            )
            for status in RiskStatus
        }

        issue_counts = {
            status.value: sum(
                issue.status == status
                for issue in self.issues.values()
            )
            for status in IssueStatus
        }

        return {
            "total_risks": len(self.risks),
            "total_issues": len(self.issues),
            "open_issues": len(self.unresolved_issues()),
            "critical_risks": sum(
                risk.severity == Severity.CRITICAL
                and risk.status != RiskStatus.CLOSED
                for risk in self.risks.values()
            ),
            "risk_status": risk_counts,
            "issue_status": issue_counts
        }

    def export_json(self, filename: str):
        data = {
            "risks": [
                {
                    "id": r.risk_id,
                    "title": r.title,
                    "description": r.description,
                    "probability": r.probability,
                    "impact": r.impact,
                    "exposure": r.exposure,
                    "severity": r.severity.name,
                    "owner": r.owner,
                    "status": r.status.value,
                    "mitigation": r.mitigation,
                    "contingency": r.contingency
                }
                for r in self.risks.values()
            ],
            "issues": [
                {
                    "id": i.issue_id,
                    "title": i.title,
                    "description": i.description,
                    "severity": i.severity.name,
                    "priority": i.priority.name,
                    "owner": i.owner,
                    "source_risk_id": i.source_risk_id,
                    "status": i.status.value,
                    "resolution": i.resolution
                }
                for i in self.issues.values()
            ]
        }

        # Exclusive file creation prevents accidental overwriting.
        with open(filename, "x", encoding="utf-8") as file:
            json.dump(data, file, indent=4)


def demonstrate():
    manager = RiskIssueManager()

    # A possible future event is recorded as a risk.
    infrastructure_risk = Risk(
        title="Cloud infrastructure outage",
        description="The primary cloud region may become unavailable.",
        probability=3,
        impact=5,
        owner="Infrastructure Team",
        category="Technology",
        mitigation="Configure multi-region redundancy.",
        contingency="Activate the secondary cloud region."
    )

    manager.add_risk(infrastructure_risk)
    infrastructure_risk.assess()
    infrastructure_risk.start_mitigation()

    # A current failure is recorded as an issue.
    database_issue = Issue(
        title="Production database connection failure",
        description="The production application cannot connect to the database.",
        severity=Severity.CRITICAL,
        priority=Priority.URGENT,
        owner="Database Team"
    )

    manager.add_issue(database_issue)
    database_issue.start()
    database_issue.resolve(
        "Restored database connectivity and verified application transactions."
    )
    database_issue.close()

    # A previously identified risk becomes an issue when it materializes.
    security_risk = Risk(
        title="Unauthorized access attempt",
        description="An external actor may exploit weak authentication.",
        probability=4,
        impact=5,
        owner="Security Team",
        category="Cybersecurity",
        mitigation="Enforce multi-factor authentication.",
        contingency="Revoke compromised credentials and isolate affected systems."
    )

    manager.add_risk(security_risk)
    security_risk.assess()

    materialized_issue = manager.convert_risk_to_issue(
        risk_id=security_risk.risk_id,
        issue_title="Unauthorized login detected",
        issue_description="An unauthorized login attempt was confirmed in security logs."
    )

    materialized_issue.start()

    print("\nHIGHEST PRIORITY RISKS")
    for risk in manager.highest_risks():
        print(
            f"{risk.title}: exposure={risk.exposure}, "
            f"severity={risk.severity.name}, "
            f"status={risk.status.value}"
        )

    print("\nUNRESOLVED ISSUES")
    for issue in manager.unresolved_issues():
        print(
            f"{issue.title}: priority={issue.priority.name}, "
            f"status={issue.status.value}"
        )

    print("\nMANAGEMENT DASHBOARD")
    print(json.dumps(manager.dashboard(), indent=4))

    print("\nRISK-TO-ISSUE TRACEABILITY")
    print({
        "risk_id": security_risk.risk_id,
        "issue_id": materialized_issue.issue_id,
        "relationship": "Risk materialized into issue"
    })

    # Verify the fundamental distinction and state management.
    assert infrastructure_risk.exposure == 15
    assert infrastructure_risk.severity == Severity.HIGH
    assert database_issue.status == IssueStatus.CLOSED
    assert materialized_issue.source_risk_id == security_risk.risk_id
    assert materialized_issue.status == IssueStatus.IN_PROGRESS

    try:
        Issue(
            title="",
            description="Invalid issue",
            severity=Severity.LOW,
            priority=Priority.LOW,
            owner="Team"
        )
    except ValueError as error:
        print("\nEXPECTED VALIDATION ERROR:", error)

    print("\nAll validation assertions passed.")


if __name__ == "__main__":
    demonstrate()
