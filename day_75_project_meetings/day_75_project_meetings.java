import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/*
 * PROJECT MEETING MANAGEMENT SYSTEM
 *
 * Enterprise-oriented meeting coordination model.
 * Features:
 * - Immutable domain identities
 * - Meeting lifecycle management
 * - Scheduling conflict detection
 * - Reviewable decisions and action ownership
 * - Policy-driven validation
 * - Meeting performance reporting
 */

public class ProjectMeetingManagement {

    enum MeetingStatus {
        SCHEDULED,
        IN_PROGRESS,
        COMPLETED,
        CANCELLED
    }

    enum ActionStatus {
        OPEN,
        IN_PROGRESS,
        BLOCKED,
        COMPLETED
    }

    enum Priority {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }

    enum ParticipantRole {
        ORGANIZER,
        CHAIRPERSON,
        MEMBER,
        OBSERVER
    }

    static class MeetingException extends RuntimeException {
        MeetingException(String message) {
            super(message);
        }
    }

    static class ValidationException extends MeetingException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class StateException extends MeetingException {
        StateException(String message) {
            super(message);
        }
    }

    record Participant(
        String id,
        String name,
        String email,
        ParticipantRole role
    ) {
        Participant {
            requireText(id, "Participant ID");
            requireText(name, "Participant name");
            requireText(email, "Email");
            Objects.requireNonNull(role);

            if (!email.matches("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$")) {
                throw new ValidationException("Invalid email address.");
            }
        }
    }

    record AgendaItem(
        String id,
        String title,
        String ownerId,
        int durationMinutes,
        Priority priority
    ) {
        AgendaItem {
            requireText(id, "Agenda ID");
            requireText(title, "Agenda title");
            requireText(ownerId, "Agenda owner");
            Objects.requireNonNull(priority);

            if (durationMinutes <= 0) {
                throw new ValidationException(
                    "Agenda duration must be positive."
                );
            }
        }
    }

    record Decision(
        String id,
        String description,
        String recordedBy,
        String rationale,
        Instant recordedAt
    ) {
        Decision {
            requireText(description, "Decision");
            requireText(recordedBy, "Decision owner");
            Objects.requireNonNull(recordedAt);
        }
    }

    record ActionItem(
        String id,
        String description,
        String assigneeId,
        Instant dueDate,
        Priority priority,
        ActionStatus status,
        String completionNotes
    ) {
        ActionItem {
            requireText(id, "Action ID");
            requireText(description, "Action description");
            requireText(assigneeId, "Action owner");
            Objects.requireNonNull(dueDate);
            Objects.requireNonNull(priority);
            Objects.requireNonNull(status);
            completionNotes = completionNotes == null
                ? "" : completionNotes;
        }

        ActionItem update(
            ActionStatus newStatus,
            String evidence
        ) {
            if (status == ActionStatus.COMPLETED) {
                throw new StateException(
                    "Completed actions cannot be reopened."
                );
            }

            if (
                newStatus == ActionStatus.COMPLETED &&
                (evidence == null || evidence.isBlank())
            ) {
                throw new ValidationException(
                    "Completion evidence is required."
                );
            }

            return new ActionItem(
                id,
                description,
                assigneeId,
                dueDate,
                priority,
                newStatus,
                evidence
            );
        }
    }

    static class MeetingPolicy {
        private final int maximumDuration;
        private final int maximumParticipants;
        private final int minimumAgendaItems;
        private final boolean requireMinutes;

        MeetingPolicy(
            int maximumDuration,
            int maximumParticipants,
            int minimumAgendaItems,
            boolean requireMinutes
        ) {
            if (
                maximumDuration <= 0 ||
                maximumParticipants <= 0 ||
                minimumAgendaItems < 0
            ) {
                throw new ValidationException(
                    "Invalid meeting policy."
                );
            }

            this.maximumDuration = maximumDuration;
            this.maximumParticipants = maximumParticipants;
            this.minimumAgendaItems = minimumAgendaItems;
            this.requireMinutes = requireMinutes;
        }

        List<String> validate(Meeting meeting) {
            List<String> violations = new ArrayList<>();

            if (meeting.durationMinutes > maximumDuration) {
                violations.add("Maximum meeting duration exceeded.");
            }

            if (meeting.participants.size() > maximumParticipants) {
                violations.add("Participant limit exceeded.");
            }

            if (meeting.agenda.size() < minimumAgendaItems) {
                violations.add("Insufficient agenda items.");
            }

            return violations;
        }

        void validateClosure(Meeting meeting, String minutes) {
            if (meeting.status != MeetingStatus.IN_PROGRESS) {
                throw new StateException(
                    "Only active meetings can close."
                );
            }

            if (
                requireMinutes &&
                (minutes == null || minutes.isBlank())
            ) {
                throw new ValidationException(
                    "Meeting minutes are mandatory."
                );
            }
        }
    }

    static class Meeting {
        final String id;
        final String title;
        final String project;
        final String organizerId;
        final Instant scheduledAt;
        final int durationMinutes;
        final String location;

        private MeetingStatus status = MeetingStatus.SCHEDULED;

        private final Map<String, Participant> participants =
            new HashMap<>();

        private final List<AgendaItem> agenda =
            new ArrayList<>();

        private final List<Decision> decisions =
            new ArrayList<>();

        private final Map<String, ActionItem> actions =
            new HashMap<>();

        private final Set<String> attendees = new HashSet<>();

        private String minutes = "";
        private long revision = 0;

        Meeting(
            String id,
            String title,
            String project,
            String organizerId,
            Instant scheduledAt,
            int durationMinutes,
            String location,
            List<Participant> participants
        ) {
            this.id = requireText(id, "Meeting ID");
            this.title = requireText(title, "Meeting title");
            this.project = requireText(project, "Project");
            this.organizerId = requireText(
                organizerId, "Organizer ID"
            );

            this.scheduledAt = Objects.requireNonNull(scheduledAt);
            this.location = requireText(location, "Location");

            if (durationMinutes <= 0) {
                throw new ValidationException(
                    "Duration must be positive."
                );
            }

            this.durationMinutes = durationMinutes;

            for (Participant participant : participants) {
                if (
                    this.participants.putIfAbsent(
                        participant.id(), participant
                    ) != null
                ) {
                    throw new ValidationException(
                        "Duplicate participant."
                    );
                }
            }

            if (!this.participants.containsKey(organizerId)) {
                throw new ValidationException(
                    "Organizer must be a participant."
                );
            }
        }

        Instant endTime() {
            return scheduledAt.plus(
                Duration.ofMinutes(durationMinutes)
            );
        }

        MeetingStatus status() {
            return status;
        }

        long revision() {
            return revision;
        }

        void addAgendaItem(AgendaItem item) {
            requireStatus(MeetingStatus.SCHEDULED);
            requireParticipant(item.ownerId());

            if (agenda.stream().anyMatch(
                existing -> existing.id().equals(item.id())
            )) {
                throw new ValidationException(
                    "Duplicate agenda item."
                );
            }

            agenda.add(item);
            revision++;
        }

        void markAttendance(String participantId) {
            if (
                status != MeetingStatus.SCHEDULED &&
                status != MeetingStatus.IN_PROGRESS
            ) {
                throw new StateException("Attendance is closed.");
            }

            requireParticipant(participantId);
            attendees.add(participantId);
            revision++;
        }

        void start(MeetingPolicy policy) {
            requireStatus(MeetingStatus.SCHEDULED);

            List<String> errors = policy.validate(this);

            if (!errors.isEmpty()) {
                throw new ValidationException(
                    String.join("; ", errors)
                );
            }

            status = MeetingStatus.IN_PROGRESS;
            revision++;
        }

        Decision recordDecision(
            String description,
            String recordedBy,
            String rationale
        ) {
            requireStatus(MeetingStatus.IN_PROGRESS);
            requireParticipant(recordedBy);

            Decision decision = new Decision(
                UUID.randomUUID().toString(),
                description,
                recordedBy,
                rationale,
                Instant.now()
            );

            decisions.add(decision);
            revision++;
            return decision;
        }

        ActionItem createAction(
            String description,
            String assigneeId,
            Instant dueDate,
            Priority priority
        ) {
            requireStatus(MeetingStatus.IN_PROGRESS);
            requireParticipant(assigneeId);

            if (dueDate == null || priority == null) {
                throw new ValidationException(
                    "Action deadline and priority are required."
                );
            }

            ActionItem action = new ActionItem(
                UUID.randomUUID().toString(),
                description,
                assigneeId,
                dueDate,
                priority,
                ActionStatus.OPEN,
                ""
            );

            actions.put(action.id(), action);
            revision++;
            return action;
        }

        void updateAction(
            String actionId,
            ActionStatus status,
            String evidence
        ) {
            ActionItem existing = actions.get(actionId);

            if (existing == null) {
                throw new ValidationException(
                    "Action item not found."
                );
            }

            actions.put(
                actionId,
                existing.update(status, evidence)
            );

            revision++;
        }

        void close(String meetingMinutes, MeetingPolicy policy) {
            policy.validateClosure(this, meetingMinutes);

            minutes = meetingMinutes.trim();
            status = MeetingStatus.COMPLETED;
            revision++;
        }

        void cancel(String reason) {
            if (
                status == MeetingStatus.COMPLETED ||
                status == MeetingStatus.CANCELLED
            ) {
                throw new StateException(
                    "Meeting cannot be cancelled."
                );
            }

            minutes = "Cancelled: " + requireText(
                reason, "Cancellation reason"
            );

            status = MeetingStatus.CANCELLED;
            revision++;
        }

        private void requireStatus(MeetingStatus expected) {
            if (status != expected) {
                throw new StateException(
                    "Expected " + expected + ", found " + status
                );
            }
        }

        private void requireParticipant(String participantId) {
            if (!participants.containsKey(participantId)) {
                throw new ValidationException(
                    "Participant does not belong to meeting."
                );
            }
        }

        List<ActionItem> actionSnapshot() {
            return List.copyOf(actions.values());
        }

        List<Decision> decisionSnapshot() {
            return List.copyOf(decisions);
        }

        List<AgendaItem> agendaSnapshot() {
            return List.copyOf(agenda);
        }

        int participantCount() {
            return participants.size();
        }

        int attendanceCount() {
            return attendees.size();
        }

        String getMinutes() {
            return minutes;
        }
    }

    record ProjectReport(
        String project,
        long meetingCount,
        long completedMeetings,
        long cancelledMeetings,
        long decisionCount,
        long totalActions,
        long completedActions,
        long overdueActions
    ) {}

    static class MeetingManagementService {
        private final Map<String, Meeting> meetings =
            new HashMap<>();

        private final MeetingPolicy policy;

        MeetingManagementService(MeetingPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        void schedule(Meeting meeting) {
            if (meetings.containsKey(meeting.id)) {
                throw new ValidationException(
                    "Duplicate meeting ID."
                );
            }

            for (Meeting existing : meetings.values()) {
                if (
                    !existing.organizerId.equals(meeting.organizerId) ||
                    (
                        existing.status() != MeetingStatus.SCHEDULED &&
                        existing.status() != MeetingStatus.IN_PROGRESS
                    )
                ) {
                    continue;
                }

                boolean overlap =
                    meeting.scheduledAt.isBefore(existing.endTime()) &&
                    existing.scheduledAt.isBefore(meeting.endTime());

                if (overlap) {
                    throw new ValidationException(
                        "Organizer scheduling conflict."
                    );
                }
            }

            List<String> errors = policy.validate(meeting);

            if (!errors.isEmpty()) {
                throw new ValidationException(
                    String.join("; ", errors)
                );
            }

            meetings.put(meeting.id, meeting);
        }

        Meeting get(String id) {
            Meeting meeting = meetings.get(id);

            if (meeting == null) {
                throw new ValidationException("Meeting not found.");
            }

            return meeting;
        }

        List<Meeting> upcoming(Instant reference) {
            return meetings.values().stream()
                .filter(m -> m.status() == MeetingStatus.SCHEDULED)
                .filter(m -> !m.scheduledAt.isBefore(reference))
                .sorted(Comparator.comparing(m -> m.scheduledAt))
                .toList();
        }

        List<ActionItem> overdueActions(Instant reference) {
            return meetings.values().stream()
                .flatMap(m -> m.actionSnapshot().stream())
                .filter(a ->
                    a.dueDate().isBefore(reference) &&
                    a.status() != ActionStatus.COMPLETED
                )
                .toList();
        }

        ProjectReport report(String project) {
            List<Meeting> selected = meetings.values().stream()
                .filter(m -> m.project.equals(project))
                .toList();

            long completed = selected.stream()
                .filter(m -> m.status() == MeetingStatus.COMPLETED)
                .count();

            long cancelled = selected.stream()
                .filter(m -> m.status() == MeetingStatus.CANCELLED)
                .count();

            long decisions = selected.stream()
                .mapToLong(m -> m.decisionSnapshot().size())
                .sum();

            List<ActionItem> actions = selected.stream()
                .flatMap(m -> m.actionSnapshot().stream())
                .toList();

            long completedActions = actions.stream()
                .filter(a -> a.status() == ActionStatus.COMPLETED)
                .count();

            long overdue = actions.stream()
                .filter(a ->
                    a.status() != ActionStatus.COMPLETED &&
                    a.dueDate().isBefore(Instant.now())
                )
                .count();

            return new ProjectReport(
                project,
                selected.size(),
                completed,
                cancelled,
                decisions,
                actions.size(),
                completedActions,
                overdue
            );
        }

        void printMeeting(Meeting meeting) {
            System.out.println("\nMEETING DETAILS");
            System.out.println("Title: " + meeting.title);
            System.out.println("Project: " + meeting.project);
            System.out.println("Status: " + meeting.status());
            System.out.println("Revision: " + meeting.revision());
            System.out.println(
                "Attendance: " + meeting.attendanceCount() +
                "/" + meeting.participantCount()
            );

            System.out.println("\nAGENDA");

            meeting.agendaSnapshot().forEach(item ->
                System.out.println(
                    item.title() + " | " +
                    item.durationMinutes() + " minutes | " +
                    item.priority()
                )
            );

            System.out.println("\nDECISIONS");

            meeting.decisionSnapshot().forEach(decision ->
                System.out.println("- " + decision.description())
            );

            System.out.println("\nACTIONS");

            meeting.actionSnapshot().forEach(action ->
                System.out.println(
                    "- " + action.description() +
                    " | Owner: " + action.assigneeId() +
                    " | Status: " + action.status()
                )
            );
        }
    }

    static String requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new ValidationException(field + " is required.");
        }
        return value.trim();
    }

    public static void main(String[] args) {
        try {
            MeetingPolicy policy = new MeetingPolicy(
                180,
                40,
                1,
                true
            );

            MeetingManagementService service =
                new MeetingManagementService(policy);

            List<Participant> participants = List.of(
                new Participant(
                    "P001",
                    "Project Manager",
                    "manager@example.com",
                    ParticipantRole.ORGANIZER
                ),
                new Participant(
                    "P002",
                    "Technical Lead",
                    "technical@example.com",
                    ParticipantRole.MEMBER
                ),
                new Participant(
                    "P003",
                    "Business Analyst",
                    "analyst@example.com",
                    ParticipantRole.MEMBER
                )
            );

            Meeting meeting = new Meeting(
                "M001",
                "Quarterly Project Review",
                "Enterprise Platform",
                "P001",
                Instant.now().plus(Duration.ofHours(2)),
                90,
                "Conference Room A",
                participants
            );

            service.schedule(meeting);

            meeting.addAgendaItem(new AgendaItem(
                "A001",
                "Delivery milestones",
                "P001",
                20,
                Priority.HIGH
            ));

            meeting.addAgendaItem(new AgendaItem(
                "A002",
                "Technical risks",
                "P002",
                30,
                Priority.CRITICAL
            ));

            meeting.markAttendance("P001");
            meeting.markAttendance("P002");
            meeting.markAttendance("P003");

            meeting.start(policy);

            meeting.recordDecision(
                "Approve revised project delivery dates.",
                "P001",
                "Resource availability confirmed."
            );

            ActionItem action = meeting.createAction(
                "Prepare risk mitigation plan.",
                "P002",
                Instant.now().plus(Duration.ofDays(5)),
                Priority.HIGH
            );

            meeting.updateAction(
                action.id(),
                ActionStatus.IN_PROGRESS,
                ""
            );

            meeting.close(
                "Revised dates approved. Risk mitigation assigned.",
                policy
            );

            service.printMeeting(meeting);

            System.out.println("\nPROJECT REPORT");
            System.out.println(
                service.report("Enterprise Platform")
            );

            System.out.println("\nUPCOMING MEETINGS");

            service.upcoming(Instant.now()).forEach(m ->
                System.out.println(m.title + " | " + m.scheduledAt)
            );

            System.out.println("\nOVERDUE ACTIONS");

            service.overdueActions(Instant.now()).forEach(a ->
                System.out.println(a.description())
            );

            // Invalid state transition.
            try {
                meeting.start(policy);
            } catch (StateException exception) {
                System.out.println(
                    "\nExpected state protection: " +
                    exception.getMessage()
                );
            }

            // Unknown participant.
            try {
                meeting.markAttendance("UNKNOWN");
            } catch (ValidationException exception) {
                System.out.println(
                    "Expected validation: " +
                    exception.getMessage()
                );
            }

            // Duplicate meeting.
            try {
                service.schedule(meeting);
            } catch (ValidationException exception) {
                System.out.println(
                    "Expected duplicate protection: " +
                    exception.getMessage()
                );
            }

        } catch (MeetingException exception) {
            System.err.println(
                "Meeting application error: " +
                exception.getMessage()
            );
            System.exit(1);
        }
    }
}
