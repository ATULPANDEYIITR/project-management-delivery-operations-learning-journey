import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/*
 * RISK RESPONSE MANAGEMENT
 *
 * Enterprise-oriented risk response planning and governance.
 *
 * Features:
 * - Threat and opportunity response strategies.
 * - Immutable risk identification attributes.
 * - Explicit state transitions.
 * - Response approval.
 * - Action ownership and budgeting.
 * - Residual risk evaluation.
 * - Secondary risk relationships.
 * - Escalation and closure.
 * - Audit records and reporting.
 *
 * Java 17, standard library only.
 */

public class RiskResponseManagement {

    enum RiskType {
        THREAT,
        OPPORTUNITY
    }

    enum RiskState {
        IDENTIFIED,
        PLANNED,
        APPROVED,
        IN_PROGRESS,
        MONITORING,
        ESCALATED,
        CLOSED
    }

    enum Strategy {
        AVOID,
        MITIGATE,
        TRANSFER,
        ACCEPT,
        ESCALATE,
        EXPLOIT,
        ENHANCE,
        SHARE
    }

    enum ActionState {
        PENDING,
        IN_PROGRESS,
        COMPLETED,
        BLOCKED,
        CANCELLED
    }

    static class RiskException extends RuntimeException {
        RiskException(String message) {
            super(message);
        }
    }

    static class ValidationException extends RiskException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class TransitionException extends RiskException {
        TransitionException(String message) {
            super(message);
        }
    }

    static class BudgetException extends RiskException {
        BudgetException(String message) {
            super(message);
        }
    }

    record RiskDefinition(
        String title,
        String description,
        RiskType type,
        double probability,
        int impact,
        String owner,
        String category,
        double budget,
        LocalDate dueDate
    ) {
        RiskDefinition {
            Objects.requireNonNull(type, "Risk type is required.");

            if (title == null || title.isBlank()) {
                throw new ValidationException("Risk title is required.");
            }

            if (description == null || description.isBlank()) {
                throw new ValidationException(
                    "Risk description is required."
                );
            }

            if (owner == null || owner.isBlank()) {
                throw new ValidationException("Risk owner is required.");
            }

            if (!Double.isFinite(probability) ||
                probability < 0 || probability > 1) {
                throw new ValidationException(
                    "Probability must be between 0 and 1."
                );
            }

            if (impact < 1 || impact > 5) {
                throw new ValidationException(
                    "Impact must be between 1 and 5."
                );
            }

            if (!Double.isFinite(budget) || budget < 0) {
                throw new ValidationException(
                    "Budget must be non-negative."
                );
            }
        }
    }

    record ResidualAssessment(
        double probability,
        int impact,
        Instant assessedAt
    ) {
        ResidualAssessment {
            if (!Double.isFinite(probability) ||
                probability < 0 || probability > 1) {
                throw new ValidationException(
                    "Invalid residual probability."
                );
            }

            if (impact < 1 || impact > 5) {
                throw new ValidationException(
                    "Residual impact must be between 1 and 5."
                );
            }

            Objects.requireNonNull(assessedAt);
        }

        double score() {
            return probability * impact;
        }
    }

    record AuditEvent(
        UUID riskId,
        String event,
        String actor,
        Instant timestamp
    ) {}

    record RiskReport(
        UUID riskId,
        String title,
        RiskType type,
        Strategy strategy,
        RiskState state,
        double inherentScore,
        double residualScore,
        double effectiveness,
        double committedBudget
    ) {}

    static class ResponseAction {
        private final UUID id;
        private final String description;
        private final String owner;
        private final LocalDate deadline;
        private final double cost;

        private ActionState state = ActionState.PENDING;
        private Instant completedAt;

        ResponseAction(
            String description,
            String owner,
            LocalDate deadline,
            double cost
        ) {
            if (description == null || description.isBlank() ||
                owner == null || owner.isBlank()) {
                throw new ValidationException(
                    "Action description and owner are required."
                );
            }

            Objects.requireNonNull(deadline);

            if (!Double.isFinite(cost) || cost < 0) {
                throw new ValidationException(
                    "Action cost cannot be negative."
                );
            }

            this.id = UUID.randomUUID();
            this.description = description;
            this.owner = owner;
            this.deadline = deadline;
            this.cost = cost;
        }

        UUID id() {
            return id;
        }

        ActionState state() {
            return state;
        }

        double cost() {
            return cost;
        }

        LocalDate deadline() {
            return deadline;
        }

        String description() {
            return description;
        }

        void transition(ActionState next) {
            if (state == ActionState.COMPLETED ||
                state == ActionState.CANCELLED) {
                throw new TransitionException(
                    "Terminal action cannot be modified."
                );
            }

            state = Objects.requireNonNull(next);

            if (next == ActionState.COMPLETED) {
                completedAt = Instant.now();
            }
        }
    }

    static class Risk {
        private final UUID id;
        private final RiskDefinition definition;
        private final List<ResponseAction> actions = new ArrayList<>();
        private final Set<UUID> secondaryRisks = new java.util.HashSet<>();

        private Strategy strategy;
        private String responseOwner;
        private RiskState state = RiskState.IDENTIFIED;
        private ResidualAssessment residual;
        private String escalationReason;

        Risk(RiskDefinition definition) {
            this.id = UUID.randomUUID();
            this.definition = definition;
        }

        UUID id() {
            return id;
        }

        String title() {
            return definition.title();
        }

        RiskType type() {
            return definition.type();
        }

        RiskState state() {
            return state;
        }

        double inherentScore() {
            return definition.probability() * definition.impact();
        }

        double residualScore() {
            return residual == null
                ? inherentScore()
                : residual.score();
        }

        double effectiveness() {
            if (inherentScore() == 0) return 0;

            return Math.max(
                0,
                Math.min(
                    100,
                    (inherentScore() - residualScore()) /
                    inherentScore() * 100
                )
            );
        }

        double committedBudget() {
            return actions.stream()
                .filter(action -> action.state() != ActionState.CANCELLED)
                .mapToDouble(ResponseAction::cost)
                .sum();
        }
    }

    static class RiskPolicy {
        private static final Map<RiskType, Set<Strategy>> ALLOWED =
            Map.of(
                RiskType.THREAT,
                EnumSet.of(
                    Strategy.AVOID,
                    Strategy.MITIGATE,
                    Strategy.TRANSFER,
                    Strategy.ACCEPT,
                    Strategy.ESCALATE
                ),
                RiskType.OPPORTUNITY,
                EnumSet.of(
                    Strategy.EXPLOIT,
                    Strategy.ENHANCE,
                    Strategy.SHARE,
                    Strategy.ACCEPT,
                    Strategy.ESCALATE
                )
            );

        void validate(RiskType type, Strategy strategy) {
            if (!ALLOWED.get(type).contains(strategy)) {
                throw new ValidationException(
                    "Strategy " + strategy +
                    " is not permitted for " + type
                );
            }
        }

        Strategy recommend(RiskDefinition definition) {
            double score = definition.probability() *
                           definition.impact();

            if (definition.type() == RiskType.THREAT) {
                if (score >= 3.5) return Strategy.AVOID;
                if (score >= 2.0) return Strategy.MITIGATE;
                if (score >= 1.0) return Strategy.TRANSFER;
                return Strategy.ACCEPT;
            }

            if (score >= 3.0) return Strategy.EXPLOIT;
            if (score >= 1.5) return Strategy.ENHANCE;

            return Strategy.ACCEPT;
        }
    }

    static class RiskService {
        private final Map<UUID, Risk> risks = new HashMap<>();
        private final List<AuditEvent> audit = new ArrayList<>();
        private final RiskPolicy policy = new RiskPolicy();

        private void record(Risk risk, String event, String actor) {
            audit.add(
                new AuditEvent(
                    risk.id(),
                    event,
                    actor,
                    Instant.now()
                )
            );
        }

        Risk createRisk(RiskDefinition definition) {
            Risk risk = new Risk(definition);

            risks.put(risk.id(), risk);

            record(risk, "RISK_CREATED", definition.owner());

            return risk;
        }

        Risk getRisk(UUID id) {
            Risk risk = risks.get(id);

            if (risk == null) {
                throw new ValidationException("Risk not found: " + id);
            }

            return risk;
        }

        void planResponse(
            UUID riskId,
            Strategy strategy,
            String responseOwner
        ) {
            Risk risk = getRisk(riskId);

            if (risk.state != RiskState.IDENTIFIED &&
                risk.state != RiskState.PLANNED) {
                throw new TransitionException(
                    "Risk cannot be planned in its current state."
                );
            }

            if (responseOwner == null || responseOwner.isBlank()) {
                throw new ValidationException(
                    "Response owner is required."
                );
            }

            policy.validate(risk.type(), strategy);

            risk.strategy = strategy;
            risk.responseOwner = responseOwner;
            risk.state = RiskState.PLANNED;

            record(risk, "RESPONSE_PLANNED:" + strategy, responseOwner);
        }

        void approveResponse(UUID riskId, String approver) {
            Risk risk = getRisk(riskId);

            if (risk.state != RiskState.PLANNED) {
                throw new TransitionException(
                    "Only planned responses can be approved."
                );
            }

            if (approver == null || approver.isBlank()) {
                throw new ValidationException(
                    "Approver identity is required."
                );
            }

            risk.state = RiskState.APPROVED;

            record(risk, "RESPONSE_APPROVED", approver);
        }

        ResponseAction addAction(
            UUID riskId,
            String description,
            String owner,
            LocalDate deadline,
            double cost
        ) {
            Risk risk = getRisk(riskId);

            if (risk.state != RiskState.PLANNED &&
                risk.state != RiskState.APPROVED &&
                risk.state != RiskState.IN_PROGRESS) {
                throw new TransitionException(
                    "A response must be planned before actions are added."
                );
            }

            ResponseAction action = new ResponseAction(
                description,
                owner,
                deadline,
                cost
            );

            double proposed = risk.committedBudget() + cost;

            if (proposed > risk.definition.budget() + 0.000001) {
                throw new BudgetException(
                    "Response budget exceeded. Committed: " +
                    proposed + ", available: " +
                    risk.definition.budget()
                );
            }

            risk.actions.add(action);

            record(risk, "ACTION_ADDED:" + action.id(), owner);

            return action;
        }

        void updateAction(
            UUID riskId,
            UUID actionId,
            ActionState state,
            String actor
        ) {
            Risk risk = getRisk(riskId);

            ResponseAction action = risk.actions.stream()
                .filter(item -> item.id().equals(actionId))
                .findFirst()
                .orElseThrow(
                    () -> new ValidationException("Action not found.")
                );

            action.transition(state);

            if (state == ActionState.IN_PROGRESS) {
                risk.state = RiskState.IN_PROGRESS;
            }

            boolean allFinished = !risk.actions.isEmpty() &&
                risk.actions.stream().allMatch(item ->
                    item.state() == ActionState.COMPLETED ||
                    item.state() == ActionState.CANCELLED
                );

            if (allFinished) {
                risk.state = RiskState.MONITORING;
            }

            record(
                risk,
                "ACTION_STATE_CHANGED:" + state,
                actor
            );
        }

        void assessResidualRisk(
            UUID riskId,
            double probability,
            int impact,
            String assessor
        ) {
            Risk risk = getRisk(riskId);

            risk.residual = new ResidualAssessment(
                probability,
                impact,
                Instant.now()
            );

            record(risk, "RESIDUAL_ASSESSED", assessor);
        }

        void linkSecondaryRisk(
            UUID parentId,
            UUID secondaryId
        ) {
            Risk parent = getRisk(parentId);
            getRisk(secondaryId);

            if (parentId.equals(secondaryId)) {
                throw new ValidationException(
                    "A risk cannot be linked to itself."
                );
            }

            parent.secondaryRisks.add(secondaryId);

            record(
                parent,
                "SECONDARY_RISK_LINKED:" + secondaryId,
                "Risk Manager"
            );
        }

        void escalate(UUID riskId, String reason, String actor) {
            Risk risk = getRisk(riskId);

            if (reason == null || reason.isBlank()) {
                throw new ValidationException(
                    "Escalation reason is required."
                );
            }

            risk.escalationReason = reason;
            risk.state = RiskState.ESCALATED;

            record(risk, "RISK_ESCALATED:" + reason, actor);
        }

        void closeRisk(UUID riskId, String actor) {
            Risk risk = getRisk(riskId);

            boolean unfinished = risk.actions.stream().anyMatch(
                action ->
                    action.state() != ActionState.COMPLETED &&
                    action.state() != ActionState.CANCELLED
            );

            if (unfinished) {
                throw new TransitionException(
                    "Outstanding response actions prevent closure."
                );
            }

            risk.state = RiskState.CLOSED;

            record(risk, "RISK_CLOSED", actor);
        }

        List<RiskReport> generateReport() {
            return risks.values().stream()
                .map(risk -> new RiskReport(
                    risk.id(),
                    risk.title(),
                    risk.type(),
                    risk.strategy,
                    risk.state,
                    risk.inherentScore(),
                    risk.residualScore(),
                    risk.effectiveness(),
                    risk.committedBudget()
                ))
                .sorted(
                    Comparator.comparingDouble(
                        RiskReport::residualScore
                    ).reversed()
                )
                .toList();
        }

        List<ResponseAction> overdueActions(LocalDate referenceDate) {
            return risks.values().stream()
                .flatMap(risk -> risk.actions.stream())
                .filter(action ->
                    action.deadline().isBefore(referenceDate) &&
                    action.state() != ActionState.COMPLETED &&
                    action.state() != ActionState.CANCELLED
                )
                .toList();
        }

        List<AuditEvent> auditLog() {
            return List.copyOf(audit);
        }
    }

    static double expectedMonetaryValue(
        double probability,
        double financialImpact
    ) {
        if (!Double.isFinite(probability) ||
            probability < 0 || probability > 1) {
            throw new ValidationException(
                "Invalid probability for EMV."
            );
        }

        if (!Double.isFinite(financialImpact) ||
            financialImpact < 0) {
            throw new ValidationException(
                "Financial impact cannot be negative."
            );
        }

        return probability * financialImpact;
    }

    static void printReport(List<RiskReport> reports) {
        System.out.println("\nENTERPRISE RISK RESPONSE REPORT");

        System.out.printf(
            "%-35s %-14s %-14s %-12s %-12s%n",
            "RISK",
            "TYPE",
            "STRATEGY",
            "STATE",
            "RESIDUAL"
        );

        for (RiskReport report : reports) {
            System.out.printf(
                "%-35s %-14s %-14s %-12s %-12.2f%n",
                report.title(),
                report.type(),
                report.strategy(),
                report.state(),
                report.residualScore()
            );

            System.out.printf(
                "  Inherent: %.2f | Residual: %.2f | " +
                "Effectiveness: %.2f%% | Budget: %.2f%n",
                report.inherentScore(),
                report.residualScore(),
                report.effectiveness(),
                report.committedBudget()
            );
        }
    }

    public static void main(String[] args) {
        RiskService service = new RiskService();

        RiskDefinition supplierDefinition = new RiskDefinition(
            "Supplier delivery failure",
            "Infrastructure supplier may miss a delivery milestone.",
            RiskType.THREAT,
            0.60,
            5,
            "Project Manager",
            "Procurement",
            15000,
            LocalDate.now().plusDays(30)
        );

        Risk supplier = service.createRisk(supplierDefinition);

        Strategy supplierStrategy =
            service.policy.recommend(supplierDefinition);

        service.planResponse(
            supplier.id(),
            supplierStrategy,
            "Procurement Lead"
        );

        service.approveResponse(
            supplier.id(),
            "Project Sponsor"
        );

        ResponseAction alternativeSupplier = service.addAction(
            supplier.id(),
            "Qualify an alternative supplier.",
            "Procurement Lead",
            LocalDate.now().plusDays(14),
            5000
        );

        service.updateAction(
            supplier.id(),
            alternativeSupplier.id(),
            ActionState.IN_PROGRESS,
            "Procurement Lead"
        );

        service.updateAction(
            supplier.id(),
            alternativeSupplier.id(),
            ActionState.COMPLETED,
            "Procurement Lead"
        );

        service.assessResidualRisk(
            supplier.id(),
            0.20,
            3,
            "Risk Analyst"
        );

        RiskDefinition opportunityDefinition = new RiskDefinition(
            "Automated testing opportunity",
            "Automation could shorten deployment cycles.",
            RiskType.OPPORTUNITY,
            0.70,
            4,
            "Engineering Manager",
            "Technology",
            8000,
            LocalDate.now().plusDays(45)
        );

        Risk opportunity = service.createRisk(opportunityDefinition);

        service.planResponse(
            opportunity.id(),
            service.policy.recommend(opportunityDefinition),
            "Automation Lead"
        );

        service.approveResponse(
            opportunity.id(),
            "Engineering Director"
        );

        service.linkSecondaryRisk(
            supplier.id(),
            opportunity.id()
        );

        System.out.println("\nEXPECTED MONETARY VALUE");

        System.out.println(
            "Inherent exposure: " +
            expectedMonetaryValue(0.60, 100000)
        );

        System.out.println(
            "Residual exposure: " +
            expectedMonetaryValue(0.20, 60000)
        );

        printReport(service.generateReport());

        System.out.println(
            "\nOverdue actions: " +
            service.overdueActions(LocalDate.now()).size()
        );

        System.out.println(
            "Audit events: " + service.auditLog().size()
        );

        if (Math.abs(supplier.residualScore() - 0.60) > 0.000001) {
            throw new AssertionError("Residual score is incorrect.");
        }

        if (Math.abs(supplier.effectiveness() - 80.0) > 0.000001) {
            throw new AssertionError("Effectiveness is incorrect.");
        }

        try {
            service.planResponse(
                supplier.id(),
                Strategy.EXPLOIT,
                "Invalid Owner"
            );
        } catch (ValidationException error) {
            System.out.println(
                "\nEXPECTED POLICY FAILURE: " + error.getMessage()
            );
        }

        System.out.println(
            "\nEnterprise risk response processing completed."
        );
    }
}
