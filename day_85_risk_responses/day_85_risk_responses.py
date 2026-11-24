"""
RISK RESPONSES: PLANNING AND EXECUTING RESPONSES TO PROJECT RISKS

Models:
- Threat responses: Avoid, Mitigate, Transfer, Accept, Escalate.
- Opportunity responses: Exploit, Enhance, Share, Accept, Escalate.
- Risk ownership and response ownership.
- Response actions, triggers, deadlines, budgets and effectiveness.
- Residual risk and secondary risk.
- Risk exposure and expected monetary value.
- Response execution and monitoring.

Python 3.10+
Standard library only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import uuid4
import json
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s"
)

logger = logging.getLogger("risk_responses")


class RiskType(str, Enum):
    THREAT = "THREAT"
    OPPORTUNITY = "OPPORTUNITY"


class RiskStatus(str, Enum):
    IDENTIFIED = "IDENTIFIED"
    PLANNED = "PLANNED"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    MONITORING = "MONITORING"
    CLOSED = "CLOSED"
    ESCALATED = "ESCALATED"


class ThreatStrategy(str, Enum):
    AVOID = "AVOID"
    MITIGATE = "MITIGATE"
    TRANSFER = "TRANSFER"
    ACCEPT = "ACCEPT"
    ESCALATE = "ESCALATE"


class OpportunityStrategy(str, Enum):
    EXPLOIT = "EXPLOIT"
    ENHANCE = "ENHANCE"
    SHARE = "SHARE"
    ACCEPT = "ACCEPT"
    ESCALATE = "ESCALATE"


class ActionStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class RiskError(Exception):
    """Base exception for risk-management failures."""


class ValidationError(RiskError):
    pass


class InvalidTransitionError(RiskError):
    pass


class BudgetExceededError(RiskError):
    pass


@dataclass
class Risk:
    title: str
    description: str
    risk_type: RiskType
    probability: float
    impact: float
    owner: str
    category: str
    response_strategy: Optional[str] = None
    response_owner: Optional[str] = None
    status: RiskStatus = RiskStatus.IDENTIFIED
    risk_id: str = field(default_factory=lambda: str(uuid4()))
    identified_on: date = field(default_factory=date.today)
    due_date: Optional[date] = None
    response_budget: float = 0.0
    residual_probability: Optional[float] = None
    residual_impact: Optional[float] = None
    secondary_risk_ids: list[str] = field(default_factory=list)
    trigger: Optional[str] = None
    notes: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.title.strip():
            raise ValidationError("Risk title cannot be empty.")

        if not self.owner.strip():
            raise ValidationError("A risk owner is required.")

        if not 0 <= self.probability <= 1:
            raise ValidationError("Probability must be between 0 and 1.")

        if not 1 <= self.impact <= 5:
            raise ValidationError("Impact must be between 1 and 5.")

        if self.response_budget < 0:
            raise ValidationError("Response budget cannot be negative.")

        if self.due_date and self.due_date < self.identified_on:
            raise ValidationError("Due date cannot precede identification.")

    @property
    def inherent_score(self) -> float:
        return self.probability * self.impact

    @property
    def inherent_emv(self) -> float:
        """Expected monetary exposure when impact is expressed in currency."""
        return self.probability * self.impact

    @property
    def residual_score(self) -> float:
        probability = (
            self.residual_probability
            if self.residual_probability is not None
            else self.probability
        )
        impact = (
            self.residual_impact
            if self.residual_impact is not None
            else self.impact
        )
        return probability * impact

    @property
    def response_effectiveness(self) -> float:
        if self.inherent_score == 0:
            return 0.0
        reduction = self.inherent_score - self.residual_score
        return max(0.0, min(100.0, reduction / self.inherent_score * 100))


@dataclass
class ResponseAction:
    risk_id: str
    description: str
    owner: str
    deadline: date
    estimated_cost: float
    action_id: str = field(default_factory=lambda: str(uuid4()))
    status: ActionStatus = ActionStatus.PENDING
    completed_on: Optional[date] = None

    def __post_init__(self):
        if not self.description.strip() or not self.owner.strip():
            raise ValidationError("Action description and owner are required.")

        if self.estimated_cost < 0:
            raise ValidationError("Action cost cannot be negative.")


@dataclass
class RiskRegister:
    risks: dict[str, Risk] = field(default_factory=dict)
    actions: dict[str, list[ResponseAction]] = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)

    def record_event(self, risk_id: str, event: str):
        self.events.append({
            "risk_id": risk_id,
            "event": event,
            "timestamp": datetime.now().isoformat(timespec="seconds")
        })

    def add_risk(self, risk: Risk):
        if risk.risk_id in self.risks:
            raise ValidationError("Duplicate risk identifier.")

        self.risks[risk.risk_id] = risk
        self.actions[risk.risk_id] = []
        self.record_event(risk.risk_id, "Risk identified")

    def get_risk(self, risk_id: str) -> Risk:
        if risk_id not in self.risks:
            raise ValidationError(f"Unknown risk: {risk_id}")
        return self.risks[risk_id]

    def choose_strategy(self, risk_id: str, strategy: str):
        risk = self.get_risk(risk_id)

        allowed = (
            {item.value for item in ThreatStrategy}
            if risk.risk_type == RiskType.THREAT
            else {item.value for item in OpportunityStrategy}
        )

        if strategy not in allowed:
            raise ValidationError(
                f"Strategy {strategy} is not valid for {risk.risk_type.value}."
            )

        risk.response_strategy = strategy
        risk.status = RiskStatus.PLANNED
        self.record_event(risk_id, f"Strategy selected: {strategy}")

    def approve_response(self, risk_id: str, approver: str):
        risk = self.get_risk(risk_id)

        if risk.status != RiskStatus.PLANNED:
            raise InvalidTransitionError("Only planned responses can be approved.")

        if not approver.strip():
            raise ValidationError("Approver is required.")

        if not risk.response_strategy:
            raise ValidationError("A response strategy must be selected.")

        risk.status = RiskStatus.APPROVED
        self.record_event(risk_id, f"Approved by {approver}")

    def add_action(self, action: ResponseAction):
        risk = self.get_risk(action.risk_id)

        if risk.status not in {
            RiskStatus.PLANNED,
            RiskStatus.APPROVED,
            RiskStatus.IN_PROGRESS
        }:
            raise InvalidTransitionError(
                "Actions require a planned or approved response."
            )

        existing = self.actions[action.risk_id]
        total_cost = sum(item.estimated_cost for item in existing)
        total_cost += action.estimated_cost

        if total_cost > risk.response_budget:
            raise BudgetExceededError(
                f"Action cost {total_cost:.2f} exceeds budget "
                f"{risk.response_budget:.2f}."
            )

        existing.append(action)
        self.record_event(action.risk_id, f"Action added: {action.description}")

    def update_action(
        self,
        risk_id: str,
        action_id: str,
        new_status: ActionStatus
    ):
        risk = self.get_risk(risk_id)

        action = next(
            (
                item for item in self.actions[risk_id]
                if item.action_id == action_id
            ),
            None
        )

        if action is None:
            raise ValidationError("Action not found.")

        if action.status in {ActionStatus.COMPLETED, ActionStatus.CANCELLED}:
            raise InvalidTransitionError("Terminal action cannot be changed.")

        action.status = new_status

        if new_status == ActionStatus.COMPLETED:
            action.completed_on = date.today()

        if new_status == ActionStatus.IN_PROGRESS:
            risk.status = RiskStatus.IN_PROGRESS

        self.record_event(
            risk_id,
            f"Action {action_id} changed to {new_status.value}"
        )

        if (
            self.actions[risk_id]
            and all(
                item.status == ActionStatus.COMPLETED
                for item in self.actions[risk_id]
            )
        ):
            risk.status = RiskStatus.MONITORING

    def record_residual_risk(
        self,
        risk_id: str,
        probability: float,
        impact: float
    ):
        risk = self.get_risk(risk_id)

        if not 0 <= probability <= 1:
            raise ValidationError("Residual probability must be 0 to 1.")

        if not 1 <= impact <= 5:
            raise ValidationError("Residual impact must be 1 to 5.")

        risk.residual_probability = probability
        risk.residual_impact = impact

        self.record_event(
            risk_id,
            f"Residual exposure recorded: {probability:.2f} x {impact:.2f}"
        )

    def escalate(self, risk_id: str, reason: str):
        risk = self.get_risk(risk_id)
        risk.status = RiskStatus.ESCALATED
        risk.notes.append(reason)
        self.record_event(risk_id, f"Escalated: {reason}")

    def close_risk(self, risk_id: str, reason: str):
        risk = self.get_risk(risk_id)

        if not reason.strip():
            raise ValidationError("Closure reason is required.")

        incomplete = [
            action for action in self.actions[risk_id]
            if action.status not in {
                ActionStatus.COMPLETED,
                ActionStatus.CANCELLED
            }
        ]

        if incomplete:
            raise InvalidTransitionError(
                "Complete or cancel outstanding actions before closure."
            )

        risk.status = RiskStatus.CLOSED
        risk.notes.append(reason)
        self.record_event(risk_id, f"Closed: {reason}")

    def overdue_actions(self, reference_date: date = date.today()):
        return [
            action
            for actions in self.actions.values()
            for action in actions
            if action.deadline < reference_date
            and action.status not in {
                ActionStatus.COMPLETED,
                ActionStatus.CANCELLED
            }
        ]

    def ranked_risks(self):
        return sorted(
            self.risks.values(),
            key=lambda risk: risk.residual_score,
            reverse=True
        )

    def report(self):
        print("\nRISK RESPONSE REGISTER")
        print("=" * 95)

        for risk in self.ranked_risks():
            print(f"\nRisk: {risk.title}")
            print(f"ID: {risk.risk_id}")
            print(f"Type: {risk.risk_type.value}")
            print(f"Strategy: {risk.response_strategy or 'Not planned'}")
            print(f"Owner: {risk.owner}")
            print(f"Status: {risk.status.value}")
            print(f"Inherent score: {risk.inherent_score:.2f}")
            print(f"Residual score: {risk.residual_score:.2f}")
            print(f"Effectiveness: {risk.response_effectiveness:.1f}%")
            print(f"Actions: {len(self.actions[risk.risk_id])}")

    def export_json(self, filename: str):
        data = {
            "risks": [
                {
                    "risk_id": risk.risk_id,
                    "title": risk.title,
                    "type": risk.risk_type.value,
                    "probability": risk.probability,
                    "impact": risk.impact,
                    "strategy": risk.response_strategy,
                    "status": risk.status.value,
                    "inherent_score": risk.inherent_score,
                    "residual_score": risk.residual_score,
                    "actions": [
                        {
                            "action_id": action.action_id,
                            "description": action.description,
                            "owner": action.owner,
                            "deadline": action.deadline.isoformat(),
                            "cost": action.estimated_cost,
                            "status": action.status.value
                        }
                        for action in self.actions[risk.risk_id]
                    ]
                }
                for risk in self.risks.values()
            ],
            "events": self.events
        }

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

        logger.info("Risk register exported to %s", filename)


def expected_monetary_value(
    probability: float,
    financial_impact: float
) -> float:
    if not 0 <= probability <= 1:
        raise ValidationError("Probability must be between 0 and 1.")

    if financial_impact < 0:
        raise ValidationError("Financial impact cannot be negative.")

    return probability * financial_impact


def select_response(
    risk: Risk,
    budget_available: float
) -> str:
    """Simple illustrative decision rule, not a substitute for expert judgment."""

    if budget_available < 0:
        raise ValidationError("Budget cannot be negative.")

    if risk.risk_type == RiskType.THREAT:
        if risk.inherent_score >= 3.5:
            return ThreatStrategy.AVOID.value
        if risk.inherent_score >= 2.0:
            return ThreatStrategy.MITIGATE.value
        if risk.inherent_score >= 1.0:
            return ThreatStrategy.TRANSFER.value
        return ThreatStrategy.ACCEPT.value

    if risk.inherent_score >= 3.0:
        return OpportunityStrategy.EXPLOIT.value
    if risk.inherent_score >= 1.5:
        return OpportunityStrategy.ENHANCE.value
    if budget_available >= 1000:
        return OpportunityStrategy.SHARE.value

    return OpportunityStrategy.ACCEPT.value


def main():
    register = RiskRegister()

    # Threat: supplier failure may delay a software deployment.
    supplier_risk = Risk(
        title="Critical supplier delivery delay",
        description="A cloud infrastructure supplier may miss the delivery date.",
        risk_type=RiskType.THREAT,
        probability=0.60,
        impact=5,
        owner="Project Manager",
        category="Supply Chain",
        response_owner="Procurement Lead",
        response_budget=15000,
        due_date=date.today() + timedelta(days=30),
        trigger="Supplier misses the agreed milestone."
    )

    register.add_risk(supplier_risk)

    strategy = select_response(supplier_risk, 15000)
    register.choose_strategy(supplier_risk.risk_id, strategy)
    register.approve_response(supplier_risk.risk_id, "Project Sponsor")

    action = ResponseAction(
        risk_id=supplier_risk.risk_id,
        description="Qualify and test an alternative supplier.",
        owner="Procurement Lead",
        deadline=date.today() + timedelta(days=14),
        estimated_cost=5000
    )

    register.add_action(action)

    register.update_action(
        supplier_risk.risk_id,
        action.action_id,
        ActionStatus.IN_PROGRESS
    )

    register.update_action(
        supplier_risk.risk_id,
        action.action_id,
        ActionStatus.COMPLETED
    )

    register.record_residual_risk(
        supplier_risk.risk_id,
        probability=0.20,
        impact=3
    )

    # Opportunity: automation could improve project delivery.
    automation_opportunity = Risk(
        title="Automation may reduce deployment time",
        description="Automated testing may shorten release cycles.",
        risk_type=RiskType.OPPORTUNITY,
        probability=0.70,
        impact=4,
        owner="Engineering Manager",
        category="Technology",
        response_budget=8000
    )

    register.add_risk(automation_opportunity)

    register.choose_strategy(
        automation_opportunity.risk_id,
        select_response(automation_opportunity, 8000)
    )

    register.approve_response(
        automation_opportunity.risk_id,
        "Engineering Director"
    )

    print("\nEXPECTED MONETARY VALUE")
    print(
        "Supplier exposure:",
        expected_monetary_value(0.60, 100000)
    )

    print(
        "Post-response exposure:",
        expected_monetary_value(0.20, 60000)
    )

    register.report()

    print("\nOVERDUE ACTIONS")
    for overdue in register.overdue_actions():
        print(overdue.description)

    # Export is intentionally optional to keep execution self-contained.
    register.export_json("risk_response_register.json")

    # Basic correctness checks.
    assert supplier_risk.inherent_score == 3.0
    assert supplier_risk.residual_score == 0.6
    assert supplier_risk.response_effectiveness == 80.0
    assert expected_monetary_value(0.5, 100000) == 50000

    try:
        register.choose_strategy(
            supplier_risk.risk_id,
            OpportunityStrategy.EXPLOIT.value
        )
    except ValidationError as error:
        print("\nEXPECTED VALIDATION ERROR:", error)

    print("\nRisk response simulation completed.")


if __name__ == "__main__":
    main()
