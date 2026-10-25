import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;

public class QualityControl {
    enum Severity {
        CRITICAL, MAJOR, MINOR, OBSERVATION
    }

    enum FindingStatus {
        OPEN, FIXED, VERIFIED, ACCEPTED
    }

    enum OutputStatus {
        DRAFT, INSPECTION, REWORK, RELEASED, REJECTED
    }

    record Requirement(String id, String description, boolean mandatory) {
        Requirement {
            if (id == null || id.isBlank() ||
                description == null || description.isBlank()) {
                throw new IllegalArgumentException(
                    "Requirement ID and description are required."
                );
            }
        }
    }

    record AuditEvent(
        Instant timestamp,
        String action,
        String actor,
        String details
    ) {}

    record CheckResult(boolean passed, String evidence) {
        CheckResult {
            evidence = evidence == null ? "" : evidence;
        }
    }

    static final class QualityException extends RuntimeException {
        QualityException(String message) {
            super(message);
        }
    }

    static final class Finding {
        private final String id = UUID.randomUUID().toString();
        private final String requirementId;
        private final Severity severity;
        private final String description;
        private final String evidence;
        private FindingStatus status = FindingStatus.OPEN;

        Finding(
            String requirementId,
            Severity severity,
            String description,
            String evidence
        ) {
            this.requirementId = Objects.requireNonNull(requirementId);
            this.severity = Objects.requireNonNull(severity);
            this.description = Objects.requireNonNull(description);
            this.evidence = evidence == null ? "" : evidence;
        }

        boolean blocksRelease() {
            return status == FindingStatus.OPEN &&
                EnumSet.of(Severity.CRITICAL, Severity.MAJOR).contains(severity);
        }

        void markFixed() {
            if (status != FindingStatus.OPEN &&
                status != FindingStatus.ACCEPTED) {
                throw new QualityException("Finding cannot be marked fixed.");
            }
            status = FindingStatus.FIXED;
        }

        void verify() {
            if (status != FindingStatus.FIXED) {
                throw new QualityException("Only fixed findings can be verified.");
            }
            status = FindingStatus.VERIFIED;
        }

        String reportLine() {
            return "[" + severity + "] " + requirementId + ": " +
                description + " | evidence=" + evidence +
                " | status=" + status;
        }
    }

    record Inspection(
        String id,
        String inspector,
        Instant inspectedAt,
        List<Finding> findings
    ) {
        Inspection {
            findings = List.copyOf(findings);
        }

        boolean passed() {
            return findings.stream().noneMatch(Finding::blocksRelease);
        }
    }

    static final class Output {
        private final String id;
        private final String name;
        private final String version;
        private final Map<String, Requirement> requirements;
        private final List<Inspection> inspections = new ArrayList<>();
        private final List<AuditEvent> audit = new ArrayList<>();
        private OutputStatus status = OutputStatus.DRAFT;

        Output(
            String id,
            String name,
            String version,
            List<Requirement> requirements
        ) {
            if (id == null || id.isBlank() ||
                name == null || name.isBlank() ||
                version == null || version.isBlank()) {
                throw new IllegalArgumentException(
                    "Output identity, name, and version are required."
                );
            }
            if (requirements == null || requirements.isEmpty()) {
                throw new IllegalArgumentException(
                    "At least one quality requirement is required."
                );
            }

            this.id = id;
            this.name = name;
            this.version = version;
            Map<String, Requirement> indexed = new LinkedHashMap<>();
            for (Requirement requirement : requirements) {
                if (indexed.putIfAbsent(requirement.id(), requirement) != null) {
                    throw new IllegalArgumentException(
                        "Duplicate requirement: " + requirement.id()
                    );
                }
            }
            this.requirements = Collections.unmodifiableMap(indexed);
        }

        Inspection inspect(String inspector, Map<String, CheckResult> results) {
            if (status == OutputStatus.RELEASED || status == OutputStatus.REJECTED) {
                throw new QualityException("Terminal output cannot be inspected.");
            }
            if (inspector == null || inspector.isBlank()) {
                throw new IllegalArgumentException("Inspector is required.");
            }
            Objects.requireNonNull(results, "Inspection results are required.");

            for (String requirementId : results.keySet()) {
                if (!requirements.containsKey(requirementId)) {
                    throw new IllegalArgumentException(
                        "Unknown requirement: " + requirementId
                    );
                }
            }

            List<Finding> findings = new ArrayList<>();
            for (Requirement requirement : requirements.values()) {
                CheckResult result = results.get(requirement.id());
                if (result == null) {
                    if (requirement.mandatory()) {
                        findings.add(new Finding(
                            requirement.id(),
                            Severity.MAJOR,
                            "Mandatory requirement was not checked.",
                            ""
                        ));
                    }
                    continue;
                }

                if (!result.passed()) {
                    findings.add(new Finding(
                        requirement.id(),
                        requirement.mandatory() ? Severity.MAJOR : Severity.MINOR,
                        requirement.description(),
                        result.evidence()
                    ));
                }
            }

            Inspection inspection = new Inspection(
                UUID.randomUUID().toString(),
                inspector,
                Instant.now(),
                findings
            );

            inspections.add(inspection);
            status = inspection.passed()
                ? OutputStatus.INSPECTION
                : OutputStatus.REWORK;

            record("INSPECTION", inspector,
                "Finding count=" + findings.size() +
                ", passed=" + inspection.passed());

            return inspection;
        }

        void release(String approver) {
            if (inspections.isEmpty() ||
                status != OutputStatus.INSPECTION ||
                !inspections.get(inspections.size() - 1).passed()) {
                throw new QualityException(
                    "Latest inspection must pass before release."
                );
            }

            boolean unresolved = inspections.stream()
                .flatMap(inspection -> inspection.findings().stream())
                .anyMatch(Finding::blocksRelease);

            if (unresolved) {
                throw new QualityException(
                    "Unresolved critical or major findings block release."
                );
            }
            if (approver == null || approver.isBlank()) {
                throw new IllegalArgumentException("Approver is required.");
            }

            status = OutputStatus.RELEASED;
            record("RELEASE", approver, "Version=" + version);
        }

        void reject(String actor, String reason) {
            if (status == OutputStatus.RELEASED) {
                throw new QualityException(
                    "Released output cannot be rejected retroactively."
                );
            }
            if (actor == null || actor.isBlank() ||
                reason == null || reason.isBlank()) {
                throw new IllegalArgumentException(
                    "Rejection actor and reason are required."
                );
            }
            status = OutputStatus.REJECTED;
            record("REJECTION", actor, reason);
        }

        private void record(String action, String actor, String details) {
            audit.add(new AuditEvent(Instant.now(), action, actor, details));
        }

        String report() {
            StringBuilder builder = new StringBuilder();
            builder.append("Output: ").append(name).append('\n');
            builder.append("ID: ").append(id).append('\n');
            builder.append("Version: ").append(version).append('\n');
            builder.append("Status: ").append(status).append('\n');

            for (int i = 0; i < inspections.size(); i++) {
                Inspection inspection = inspections.get(i);
                builder.append("\nInspection ").append(i + 1)
                    .append(" by ").append(inspection.inspector())
                    .append(": ").append(inspection.passed() ? "PASS" : "FAIL")
                    .append('\n');

                inspection.findings().forEach(finding ->
                    builder.append("  ")
                        .append(finding.reportLine())
                        .append('\n')
                );
            }

            builder.append("\nAudit trail\n");
            audit.forEach(event -> builder.append(event.timestamp())
                .append(" | ").append(event.action())
                .append(" | ").append(event.actor())
                .append(" | ").append(event.details())
                .append('\n'));

            return builder.toString();
        }
    }

    private static void runValidationTests() {
        List<Requirement> requirements = List.of(
            new Requirement("Q1", "Completeness", true),
            new Requirement("Q2", "Reconciliation", true),
            new Requirement("Q3", "Formatting", false)
        );

        Output output = new Output("TEST-1", "Test report", "1.0", requirements);
        Inspection inspection = output.inspect("reviewer", Map.of(
            "Q1", new CheckResult(true, "Checklist passed"),
            "Q2", new CheckResult(false, "Difference: 20"),
            "Q3", new CheckResult(true, "Style checked")
        ));

        if (inspection.passed()) {
            throw new IllegalStateException("Failed reconciliation was accepted.");
        }

        try {
            output.release("manager");
            throw new IllegalStateException("Release should have been blocked.");
        } catch (QualityException expected) {
            System.out.println("Release-gate validation passed.");
        }

        try {
            output.inspect("reviewer", Map.of(
                "UNKNOWN", new CheckResult(true, "Invalid ID")
            ));
            throw new IllegalStateException("Unknown requirement was accepted.");
        } catch (IllegalArgumentException expected) {
            System.out.println("Requirement validation passed.");
        }
    }

    public static void main(String[] args) {
        runValidationTests();

        List<Requirement> requirements = List.of(
            new Requirement("Q1", "All required report sections are present", true),
            new Requirement("Q2", "Reported totals match source records", true),
            new Requirement("Q3", "Charts use approved labels and units", true),
            new Requirement("Q4", "Optional design enhancement is present", false)
        );

        Output output = new Output(
            "OUT-2026-055",
            "Enterprise Service Performance Report",
            "4.2",
            requirements
        );

        Inspection inspection = output.inspect("quality-engineer", Map.of(
            "Q1", new CheckResult(true, "Section checklist passed"),
            "Q2", new CheckResult(false, "Report total 76500; source total 76440"),
            "Q3", new CheckResult(true, "Labels and units verified"),
            "Q4", new CheckResult(true, "Optional enhancement checked")
        ));

        System.out.println("\nInitial inspection: " +
            (inspection.passed() ? "PASS" : "FAIL"));

        try {
            output.release("quality-manager");
        } catch (QualityException exception) {
            System.out.println("Release blocked: " + exception.getMessage());
        }

        System.out.println("\n" + output.report());
    }
}
