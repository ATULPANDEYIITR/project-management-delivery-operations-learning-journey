import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

/*
 * Leadership in Project Management
 *
 * Enterprise project leadership management model.
 *
 * Covers:
 * - Leadership styles
 * - Situational leadership
 * - Delegation and accountability
 * - Team capacity management
 * - Stakeholder engagement
 * - Risk ownership
 * - Conflict management
 * - Leadership decisions
 * - Governance and auditability
 * - Project performance evaluation
 */

public class ProjectLeadershipApp {

    enum LeadershipStyle {
        AUTOCRATIC,
        DEMOCRATIC,
        TRANSFORMATIONAL,
        TRANSACTIONAL,
        SERVANT,
        SITUATIONAL
    }

    enum SkillLevel {
        BEGINNER(1),
        DEVELOPING(2),
        COMPETENT(3),
        ADVANCED(4),
        EXPERT(5);

        private final int value;

        SkillLevel(int value) {
            this.value = value;
        }

        public int value() {
            return value;
        }
    }

    enum TaskStatus {
        NOT_STARTED,
        IN_PROGRESS,
        BLOCKED,
        COMPLETED
    }

    enum DecisionStatus {
        PROPOSED,
        APPROVED,
        REJECTED,
        DEFERRED
    }

    enum RiskLevel {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }

    static class LeadershipException extends RuntimeException {
        LeadershipException(String message) {
            super(message);
        }
    }

    static class ValidationException extends LeadershipException {
        ValidationException(String message) {
            super(message);
        }
    }

    record StakeholderEngagement(
        String stakeholderName,
        int influence,
        int interest,
        String strategy
    ) {}

    record AuditEvent(
        UUID eventId,
        String eventType,
        String description,
        Instant timestamp
    ) {}

    record LeadershipMetrics(
        int totalTasks,
        int completedTasks,
        double completionRate,
        double averageProgress,
        double averageWorkload,
        int openRisks,
        int criticalRisks
    ) {}

    static final class TeamMember {
        private final int id;
        private final String name;
        private final String role;
        private final SkillLevel skillLevel;
        private final String developmentGoal;

        private int workload;
        private int completedTasks;
        private boolean active;

        TeamMember(
            int id,
            String name,
            String role,
            SkillLevel skillLevel,
            String developmentGoal
        ) {
            if (id <= 0) {
                throw new ValidationException("Invalid member ID.");
            }

            if (name == null || name.isBlank()) {
                throw new ValidationException("Member name is required.");
            }

            this.id = id;
            this.name = name;
            this.role = Objects.requireNonNull(role);
            this.skillLevel = Objects.requireNonNull(skillLevel);
            this.developmentGoal = Objects.requireNonNull(
                developmentGoal
            );

            this.workload = 0;
            this.completedTasks = 0;
            this.active = true;
        }

        public int id() {
            return id;
        }

        public String name() {
            return name;
        }

        public String role() {
            return role;
        }

        public int workload() {
            return workload;
        }

        public int completedTasks() {
            return completedTasks;
        }

        public boolean active() {
            return active;
        }
    }

    static final class ProjectTask {
        private final int id;
        private final String title;
        private final SkillLevel requiredSkill;
        private final double estimatedHours;
        private final int priority;

        private TaskStatus status;
        private Integer assignedTo;
        private double progress;
        private long version;

        ProjectTask(
            int id,
            String title,
            SkillLevel requiredSkill,
            double estimatedHours,
            int priority
        ) {
            if (id <= 0 || title == null || title.isBlank()) {
                throw new ValidationException("Invalid task definition.");
            }

            if (estimatedHours <= 0) {
                throw new ValidationException(
                    "Estimated hours must be positive."
                );
            }

            if (priority < 1 || priority > 5) {
                throw new ValidationException("Priority must be 1-5.");
            }

            this.id = id;
            this.title = title;
            this.requiredSkill = Objects.requireNonNull(requiredSkill);
            this.estimatedHours = estimatedHours;
            this.priority = priority;

            this.status = TaskStatus.NOT_STARTED;
            this.assignedTo = null;
            this.progress = 0;
            this.version = 0;
        }

        public int id() {
            return id;
        }

        public String title() {
            return title;
        }

        public TaskStatus status() {
            return status;
        }

        public double progress() {
            return progress;
        }

        public Integer assignedTo() {
            return assignedTo;
        }

        public long version() {
            return version;
        }
    }

    static final class Stakeholder {
        private final int id;
        private final String name;
        private final int influence;
        private final int interest;
        private final String expectations;

        Stakeholder(
            int id,
            String name,
            int influence,
            int interest,
            String expectations
        ) {
            if (id <= 0 || name == null || name.isBlank()) {
                throw new ValidationException("Invalid stakeholder.");
            }

            validateRating(influence);
            validateRating(interest);

            this.id = id;
            this.name = name;
            this.influence = influence;
            this.interest = interest;
            this.expectations = Objects.requireNonNull(expectations);
        }

        private static void validateRating(int value) {
            if (value < 1 || value > 5) {
                throw new ValidationException("Rating must be 1-5.");
            }
        }
    }

    static final class ProjectRisk {
        private final int id;
        private final String description;
        private final int probability;
        private final int impact;
        private final int ownerId;
        private final String mitigation;

        private boolean open;

        ProjectRisk(
            int id,
            String description,
            int probability,
            int impact,
            int ownerId,
            String mitigation
        ) {
            if (id <= 0 || ownerId <= 0 ||
                description == null || description.isBlank()) {
                throw new ValidationException("Invalid risk.");
            }

            validateRating(probability);
            validateRating(impact);

            this.id = id;
            this.description = description;
            this.probability = probability;
            this.impact = impact;
            this.ownerId = ownerId;
            this.mitigation = Objects.requireNonNull(mitigation);
            this.open = true;
        }

        private static void validateRating(int value) {
            if (value < 1 || value > 5) {
                throw new ValidationException("Risk rating must be 1-5.");
            }
        }

        int exposure() {
            return probability * impact;
        }

        RiskLevel level() {
            int score = exposure();

            if (score >= 20) return RiskLevel.CRITICAL;
            if (score >= 12) return RiskLevel.HIGH;
            if (score >= 6) return RiskLevel.MEDIUM;

            return RiskLevel.LOW;
        }
    }

    static final class LeadershipDecision {
        private final int id;
        private final String title;
        private final String description;
        private final String owner;
        private final Instant createdAt;

        private DecisionStatus status;
        private String rationale;

        LeadershipDecision(
            int id,
            String title,
            String description,
            String owner
        ) {
            if (id <= 0 || title == null || title.isBlank() ||
                owner == null || owner.isBlank()) {
                throw new ValidationException("Invalid decision.");
            }

            this.id = id;
            this.title = title;
            this.description = Objects.requireNonNull(description);
            this.owner = owner;
            this.createdAt = Instant.now();

            this.status = DecisionStatus.PROPOSED;
        }
    }

    interface LeadershipEventListener {
        void onEvent(AuditEvent event);
    }

    static final class LeadershipEventService {
        private final List<LeadershipEventListener> listeners =
            new ArrayList<>();

        void subscribe(LeadershipEventListener listener) {
            listeners.add(Objects.requireNonNull(listener));
        }

        void publish(String type, String description) {
            AuditEvent event = new AuditEvent(
                UUID.randomUUID(),
                type,
                description,
                Instant.now()
            );

            for (LeadershipEventListener listener : listeners) {
                listener.onEvent(event);
            }
        }
    }

    static final class LeadershipPolicy {

        static LeadershipStyle selectStyle(
            SkillLevel skill,
            int urgency,
            int complexity
        ) {
            validateRating(urgency);
            validateRating(complexity);

            if (urgency >= 5) {
                return LeadershipStyle.AUTOCRATIC;
            }

            if (skill.value() <= 2) {
                return LeadershipStyle.SITUATIONAL;
            }

            if (complexity >= 4) {
                return LeadershipStyle.TRANSFORMATIONAL;
            }

            if (skill.value() >= 4) {
                return LeadershipStyle.SERVANT;
            }

            return LeadershipStyle.DEMOCRATIC;
        }

        static String stakeholderStrategy(
            int influence,
            int interest
        ) {
            validateRating(influence);
            validateRating(interest);

            if (influence >= 4 && interest >= 4) {
                return "Manage closely";
            }

            if (influence >= 4) {
                return "Keep satisfied";
            }

            if (interest >= 4) {
                return "Keep informed";
            }

            return "Monitor";
        }

        private static void validateRating(int value) {
            if (value < 1 || value > 5) {
                throw new ValidationException("Rating must be 1-5.");
            }
        }
    }

    static final class ProjectLeadershipService {
        private static final int TASK_ALLOCATION = 20;

        private final String projectName;
        private final LeadershipStyle defaultStyle;

        private final Map<Integer, TeamMember> members =
            new HashMap<>();

        private final Map<Integer, ProjectTask> tasks =
            new HashMap<>();

        private final Map<Integer, Stakeholder> stakeholders =
            new HashMap<>();

        private final Map<Integer, ProjectRisk> risks =
            new HashMap<>();

        private final Map<Integer, LeadershipDecision> decisions =
            new HashMap<>();

        private final List<AuditEvent> auditLog =
            new ArrayList<>();

        private final LeadershipEventService eventService =
            new LeadershipEventService();

        ProjectLeadershipService(
            String projectName,
            LeadershipStyle defaultStyle
        ) {
            if (projectName == null || projectName.isBlank()) {
                throw new ValidationException(
                    "Project name is required."
                );
            }

            this.projectName = projectName;
            this.defaultStyle = Objects.requireNonNull(defaultStyle);

            eventService.subscribe(auditLog::add);
        }

        void addMember(TeamMember member) {
            if (members.putIfAbsent(member.id(), member) != null) {
                throw new ValidationException("Duplicate member ID.");
            }
        }

        void addTask(ProjectTask task) {
            if (tasks.putIfAbsent(task.id(), task) != null) {
                throw new ValidationException("Duplicate task ID.");
            }
        }

        void addStakeholder(Stakeholder stakeholder) {
            if (stakeholders.putIfAbsent(
                stakeholder.id, stakeholder
            ) != null) {
                throw new ValidationException(
                    "Duplicate stakeholder ID."
                );
            }
        }

        void addRisk(ProjectRisk risk) {
            if (!members.containsKey(risk.ownerId)) {
                throw new ValidationException(
                    "Risk owner does not exist."
                );
            }

            if (risks.putIfAbsent(risk.id, risk) != null) {
                throw new ValidationException("Duplicate risk ID.");
            }
        }

        void assignTask(int taskId, int memberId) {
            ProjectTask task = tasks.get(taskId);
            TeamMember member = members.get(memberId);

            if (task == null || member == null) {
                throw new ValidationException(
                    "Task or member does not exist."
                );
            }

            if (!member.active) {
                throw new LeadershipException(
                    "Inactive members cannot receive assignments."
                );
            }

            if (task.status == TaskStatus.COMPLETED) {
                throw new LeadershipException(
                    "Completed tasks cannot be reassigned."
                );
            }

            if (member.skillLevel.value() <
                task.requiredSkill.value()) {
                throw new LeadershipException(
                    "Insufficient technical skill."
                );
            }

            int effectiveWorkload = member.workload;

            if (Objects.equals(task.assignedTo, memberId)) {
                effectiveWorkload -= TASK_ALLOCATION;
            }

            if (effectiveWorkload + TASK_ALLOCATION > 100) {
                throw new LeadershipException(
                    "Team member workload exceeds capacity."
                );
            }

            // Validate before modifying the old and new assignments.
            TeamMember previous = task.assignedTo == null
                ? null
                : members.get(task.assignedTo);

            if (previous != null) {
                previous.workload = Math.max(
                    0, previous.workload - TASK_ALLOCATION
                );
            }

            member.workload += TASK_ALLOCATION;

            task.assignedTo = memberId;
            task.status = TaskStatus.IN_PROGRESS;
            task.version++;

            eventService.publish(
                "TASK_ASSIGNED",
                task.title + " assigned to " + member.name
            );
        }

        void updateProgress(
            int taskId,
            double progress,
            long expectedVersion
        ) {
            ProjectTask task = tasks.get(taskId);

            if (task == null) {
                throw new ValidationException("Task does not exist.");
            }

            if (progress < 0 || progress > 100 ||
                Double.isNaN(progress)) {
                throw new ValidationException(
                    "Progress must be between 0 and 100."
                );
            }

            if (task.version != expectedVersion) {
                throw new LeadershipException(
                    "Concurrent task modification detected."
                );
            }

            if (task.status == TaskStatus.COMPLETED) {
                throw new LeadershipException(
                    "Task is already completed."
                );
            }

            if (task.assignedTo == null) {
                throw new LeadershipException("Task has no owner.");
            }

            if (progress < task.progress) {
                throw new ValidationException(
                    "Progress cannot decrease."
                );
            }

            TeamMember member = members.get(task.assignedTo);

            task.progress = progress;
            task.version++;

            if (progress == 100) {
                task.status = TaskStatus.COMPLETED;

                member.workload = Math.max(
                    0, member.workload - TASK_ALLOCATION
                );

                member.completedTasks++;

                eventService.publish(
                    "TASK_COMPLETED",
                    task.title + " completed by " + member.name
                );
            }
        }

        void createDecision(LeadershipDecision decision) {
            if (decisions.putIfAbsent(
                decision.id, decision
            ) != null) {
                throw new ValidationException(
                    "Duplicate decision ID."
                );
            }
        }

        void processDecision(
            int id,
            DecisionStatus status,
            String rationale
        ) {
            LeadershipDecision decision = decisions.get(id);

            if (decision == null) {
                throw new ValidationException(
                    "Decision does not exist."
                );
            }

            if (decision.status != DecisionStatus.PROPOSED) {
                throw new LeadershipException(
                    "Decision has already been processed."
                );
            }

            if (rationale == null || rationale.isBlank()) {
                throw new ValidationException(
                    "Decision rationale is mandatory."
                );
            }

            decision.status = Objects.requireNonNull(status);
            decision.rationale = rationale;

            eventService.publish(
                "DECISION_PROCESSED",
                decision.title + ": " + status
            );
        }

        void resolveConflict(
            String issue,
            List<String> options,
            String selectedOption
        ) {
            if (issue == null || issue.isBlank() ||
                options == null || options.size() < 2) {
                throw new ValidationException(
                    "Invalid conflict definition."
                );
            }

            if (!options.contains(selectedOption)) {
                throw new ValidationException(
                    "Selected option is not available."
                );
            }

            eventService.publish(
                "CONFLICT_RESOLVED",
                issue + " | " + selectedOption
            );
        }

        List<StakeholderEngagement> stakeholderReport() {
            return stakeholders.values()
                .stream()
                .map(stakeholder -> new StakeholderEngagement(
                    stakeholder.name,
                    stakeholder.influence,
                    stakeholder.interest,
                    LeadershipPolicy.stakeholderStrategy(
                        stakeholder.influence,
                        stakeholder.interest
                    )
                ))
                .sorted(
                    Comparator.comparingInt(
                        (StakeholderEngagement s) ->
                            s.influence() * s.interest()
                    ).reversed()
                )
                .collect(Collectors.toUnmodifiableList());
        }

        LeadershipMetrics calculateMetrics() {
            int completed = 0;
            int openRisks = 0;
            int criticalRisks = 0;

            double totalProgress = 0;
            double totalWorkload = 0;
            int activeMembers = 0;

            for (ProjectTask task : tasks.values()) {
                totalProgress += task.progress;

                if (task.status == TaskStatus.COMPLETED) {
                    completed++;
                }
            }

            for (TeamMember member : members.values()) {
                if (member.active) {
                    totalWorkload += member.workload;
                    activeMembers++;
                }
            }

            for (ProjectRisk risk : risks.values()) {
                if (risk.open) {
                    openRisks++;

                    if (risk.level() == RiskLevel.CRITICAL) {
                        criticalRisks++;
                    }
                }
            }

            int total = tasks.size();

            return new LeadershipMetrics(
                total,
                completed,
                total == 0 ? 0 : completed * 100.0 / total,
                total == 0 ? 0 : totalProgress / total,
                activeMembers == 0
                    ? 0
                    : totalWorkload / activeMembers,
                openRisks,
                criticalRisks
            );
        }

        void printReport() {
            LeadershipMetrics metrics = calculateMetrics();

            System.out.println("\nPROJECT LEADERSHIP REPORT");
            System.out.println("Project: " + projectName);
            System.out.println("Default leadership style: " + defaultStyle);

            System.out.println("\nTEAM");

            members.values().forEach(member ->
                System.out.printf(
                    "%s | %s | Workload: %d%% | Completed: %d%n",
                    member.name,
                    member.role,
                    member.workload,
                    member.completedTasks
                )
            );

            System.out.println("\nTASKS");

            tasks.values().forEach(task ->
                System.out.printf(
                    "%s | %s | %.1f%%%n",
                    task.title,
                    task.status,
                    task.progress
                )
            );

            System.out.println("\nRISKS");

            risks.values().forEach(risk ->
                System.out.printf(
                    "%s | Exposure: %d | Level: %s%n",
                    risk.description,
                    risk.exposure(),
                    risk.level()
                )
            );

            System.out.println("\nSTAKEHOLDER ENGAGEMENT");

            stakeholderReport().forEach(System.out::println);

            System.out.println("\nPERFORMANCE");

            System.out.printf(
                "Tasks: %d | Completed: %d | Completion: %.2f%%%n",
                metrics.totalTasks(),
                metrics.completedTasks(),
                metrics.completionRate()
            );

            System.out.printf(
                "Average progress: %.2f%% | Average workload: %.2f%%%n",
                metrics.averageProgress(),
                metrics.averageWorkload()
            );

            System.out.println(
                "Open risks: " + metrics.openRisks()
            );

            System.out.println(
                "Critical risks: " + metrics.criticalRisks()
            );

            System.out.println("\nAUDIT HISTORY");

            auditLog.forEach(event ->
                System.out.println(
                    event.timestamp() + " | " +
                    event.eventType() + " | " +
                    event.description()
                )
            );
        }
    }

    public static void main(String[] args) {
        try {
            ProjectLeadershipService project =
                new ProjectLeadershipService(
                    "Enterprise Transformation Programme",
                    LeadershipStyle.TRANSFORMATIONAL
                );

            project.addMember(new TeamMember(
                1,
                "Ananya",
                "Project Manager",
                SkillLevel.EXPERT,
                "Strategic leadership"
            ));

            project.addMember(new TeamMember(
                2,
                "Rahul",
                "Technical Lead",
                SkillLevel.ADVANCED,
                "Technical mentoring"
            ));

            project.addMember(new TeamMember(
                3,
                "Meera",
                "Business Analyst",
                SkillLevel.COMPETENT,
                "Stakeholder management"
            ));

            project.addTask(new ProjectTask(
                101,
                "Architecture assessment",
                SkillLevel.ADVANCED,
                40,
                5
            ));

            project.addTask(new ProjectTask(
                102,
                "Requirements analysis",
                SkillLevel.COMPETENT,
                30,
                4
            ));

            project.addTask(new ProjectTask(
                103,
                "Implementation planning",
                SkillLevel.ADVANCED,
                25,
                5
            ));

            project.addStakeholder(new Stakeholder(
                1,
                "Executive Sponsor",
                5,
                5,
                "Achieve strategic delivery objectives."
            ));

            project.addStakeholder(new Stakeholder(
                2,
                "Operations Manager",
                4,
                3,
                "Maintain operational continuity."
            ));

            project.addStakeholder(new Stakeholder(
                3,
                "End Users",
                2,
                5,
                "Ensure system usability."
            ));

            project.addRisk(new ProjectRisk(
                201,
                "Integration delay",
                4,
                5,
                2,
                "Introduce technical checkpoints."
            ));

            project.assignTask(101, 2);
            project.assignTask(102, 3);

            long taskVersion = project.tasks.get(101).version();

            project.updateProgress(101, 65, taskVersion);
            project.updateProgress(
                102,
                100,
                project.tasks.get(102).version()
            );

            project.createDecision(new LeadershipDecision(
                301,
                "Phased implementation",
                "Deliver functionality in controlled phases.",
                "Project Manager"
            ));

            project.processDecision(
                301,
                DecisionStatus.APPROVED,
                "Reduces implementation risk and operational disruption."
            );

            project.resolveConflict(
                "Disagreement about deployment timing",
                List.of("Full deployment", "Phased deployment"),
                "Phased deployment"
            );

            LeadershipStyle selectedStyle =
                LeadershipPolicy.selectStyle(
                    SkillLevel.COMPETENT,
                    2,
                    4
                );

            System.out.println(
                "Situational leadership recommendation: " +
                selectedStyle
            );

            project.printReport();

        } catch (LeadershipException | IllegalArgumentException error) {
            System.err.println(
                "Project leadership error: " + error.getMessage()
            );

            System.exitCode = 1;
        }
    }
}
