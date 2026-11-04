from __future__ import annotations

import json
import logging
import re
import tempfile
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import uuid4


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger("team_communication")


class Role(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    OBSERVER = "observer"


class ChannelType(Enum):
    GENERAL = "general"
    PROJECT = "project"
    ANNOUNCEMENTS = "announcements"
    INCIDENT = "incident"
    PRIVATE = "private"


class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class MessageStatus(Enum):
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class TaskStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class CommunicationError(Exception):
    pass


class ValidationError(CommunicationError):
    pass


class AuthorizationError(CommunicationError):
    pass


@dataclass
class User:
    user_id: str
    name: str
    email: str
    role: Role
    active: bool = True

    def __post_init__(self):
        if not self.name.strip():
            raise ValidationError("User name cannot be empty.")

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", self.email):
            raise ValidationError("Invalid email address.")


@dataclass
class Channel:
    channel_id: str
    name: str
    channel_type: ChannelType
    created_by: str
    members: set[str] = field(default_factory=set)
    archived: bool = False


@dataclass
class Message:
    message_id: str
    channel_id: str
    sender_id: str
    content: str
    priority: MessagePriority
    created_at: datetime
    status: MessageStatus = MessageStatus.SENT
    parent_id: Optional[str] = None
    recipients: set[str] = field(default_factory=set)
    read_by: set[str] = field(default_factory=set)
    acknowledged_by: set[str] = field(default_factory=set)
    edited_at: Optional[datetime] = None


@dataclass
class ActionItem:
    task_id: str
    message_id: str
    title: str
    owner_id: str
    due_at: datetime
    status: TaskStatus = TaskStatus.OPEN
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class TeamCommunicationSystem:
    """
    In-memory team communication and accountability platform.

    Messages are separated from action items. Reading a message does
    not automatically acknowledge it or complete an assigned task.
    """

    def __init__(self):
        self.users: dict[str, User] = {}
        self.channels: dict[str, Channel] = {}
        self.messages: dict[str, Message] = {}
        self.tasks: dict[str, ActionItem] = {}
        self.notifications: dict[str, list[dict]] = defaultdict(list)
        self.audit_log: list[dict] = []

    @staticmethod
    def _id() -> str:
        return str(uuid4())

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _audit(self, actor: str, event: str, target: str):
        self.audit_log.append({
            "actor": actor,
            "event": event,
            "target": target,
            "timestamp": self._now().isoformat()
        })

    def _require_user(self, user_id: str) -> User:
        user = self.users.get(user_id)

        if user is None or not user.active:
            raise AuthorizationError("User does not exist or is inactive.")

        return user

    def _require_membership(self, user_id: str, channel_id: str):
        user = self._require_user(user_id)
        channel = self.channels.get(channel_id)

        if channel is None or channel.archived:
            raise ValidationError("Channel is unavailable.")

        if user_id not in channel.members:
            raise AuthorizationError("Channel membership required.")

        return user, channel

    def register_user(
        self,
        name: str,
        email: str,
        role: Role = Role.MEMBER
    ) -> User:
        if any(u.email.lower() == email.lower()
               for u in self.users.values()):
            raise ValidationError("Email address already registered.")

        user = User(self._id(), name, email, role)
        self.users[user.user_id] = user
        self._audit(user.user_id, "USER_REGISTERED", user.user_id)
        return user

    def create_channel(
        self,
        creator_id: str,
        name: str,
        channel_type: ChannelType,
        member_ids: set[str]
    ) -> Channel:
        creator = self._require_user(creator_id)

        if creator.role not in (Role.ADMIN, Role.MANAGER):
            raise AuthorizationError("Only managers and administrators can create channels.")

        if not name.strip() or len(name) > 80:
            raise ValidationError("Channel name must contain 1-80 characters.")

        members = set(member_ids)
        members.add(creator_id)

        for member_id in members:
            self._require_user(member_id)

        if channel_type == ChannelType.PRIVATE and len(members) < 2:
            raise ValidationError("Private channels require at least two members.")

        channel = Channel(
            channel_id=self._id(),
            name=name.strip(),
            channel_type=channel_type,
            created_by=creator_id,
            members=members
        )

        self.channels[channel.channel_id] = channel
        self._audit(creator_id, "CHANNEL_CREATED", channel.channel_id)
        return channel

    def add_member(
        self,
        actor_id: str,
        channel_id: str,
        member_id: str
    ):
        actor, channel = self._require_membership(actor_id, channel_id)
        self._require_user(member_id)

        if actor.role not in (Role.ADMIN, Role.MANAGER):
            raise AuthorizationError("Manager privileges required.")

        channel.members.add(member_id)
        self._audit(actor_id, "MEMBER_ADDED", channel_id)

    def send_message(
        self,
        sender_id: str,
        channel_id: str,
        content: str,
        priority: MessagePriority = MessagePriority.NORMAL,
        recipients: Optional[set[str]] = None,
        parent_id: Optional[str] = None
    ) -> Message:
        sender, channel = self._require_membership(sender_id, channel_id)

        content = content.strip()

        if not content:
            raise ValidationError("Message cannot be empty.")

        if len(content) > 10000:
            raise ValidationError("Message exceeds 10,000 characters.")

        if sender.role == Role.OBSERVER:
            raise AuthorizationError("Observers cannot send messages.")

        if channel.channel_type == ChannelType.ANNOUNCEMENTS:
            if sender.role not in (Role.ADMIN, Role.MANAGER):
                raise AuthorizationError("Only managers can post announcements.")

        if parent_id:
            parent = self.messages.get(parent_id)

            if parent is None or parent.channel_id != channel_id:
                raise ValidationError("Invalid parent message.")

        target_users = set(recipients) if recipients is not None else (
            channel.members - {sender_id}
        )

        if not target_users.issubset(channel.members):
            raise AuthorizationError("Recipient is not a channel member.")

        message = Message(
            message_id=self._id(),
            channel_id=channel_id,
            sender_id=sender_id,
            content=content,
            priority=priority,
            created_at=self._now(),
            parent_id=parent_id,
            recipients=target_users
        )

        self.messages[message.message_id] = message

        for recipient_id in target_users:
            self.notifications[recipient_id].append({
                "message_id": message.message_id,
                "priority": priority.name,
                "created_at": message.created_at.isoformat(),
                "read": False
            })

        self._audit(sender_id, "MESSAGE_SENT", message.message_id)

        logger.info(
            "Message %s sent to %d recipients",
            message.message_id,
            len(target_users)
        )

        return message

    def mark_read(self, user_id: str, message_id: str):
        user = self._require_user(user_id)
        message = self.messages.get(message_id)

        if message is None:
            raise ValidationError("Message not found.")

        self._require_membership(user_id, message.channel_id)

        if user_id not in message.recipients:
            if user_id != message.sender_id:
                raise AuthorizationError("Message was not addressed to this user.")

        message.read_by.add(user_id)

        for notification in self.notifications[user_id]:
            if notification["message_id"] == message_id:
                notification["read"] = True

        self._audit(user_id, "MESSAGE_READ", message_id)

    def acknowledge(self, user_id: str, message_id: str):
        self.mark_read(user_id, message_id)
        message = self.messages[message_id]

        if user_id not in message.recipients:
            raise AuthorizationError("Only recipients can acknowledge.")

        message.acknowledged_by.add(user_id)

        if message.recipients.issubset(message.acknowledged_by):
            message.status = MessageStatus.ACKNOWLEDGED

        self._audit(user_id, "MESSAGE_ACKNOWLEDGED", message_id)

    def edit_message(
        self,
        user_id: str,
        message_id: str,
        new_content: str
    ):
        user = self._require_user(user_id)
        message = self.messages.get(message_id)

        if message is None:
            raise ValidationError("Message not found.")

        if message.sender_id != user_id and user.role != Role.ADMIN:
            raise AuthorizationError("Cannot edit another user's message.")

        new_content = new_content.strip()

        if not new_content or len(new_content) > 10000:
            raise ValidationError("Invalid message content.")

        if message.status == MessageStatus.ARCHIVED:
            raise ValidationError("Archived messages cannot be edited.")

        message.content = new_content
        message.edited_at = self._now()
        self._audit(user_id, "MESSAGE_EDITED", message_id)

    def create_action_item(
        self,
        creator_id: str,
        message_id: str,
        title: str,
        owner_id: str,
        due_at: datetime
    ) -> ActionItem:
        message = self.messages.get(message_id)

        if message is None:
            raise ValidationError("Source message not found.")

        self._require_membership(creator_id, message.channel_id)
        self._require_membership(owner_id, message.channel_id)

        if creator_id != message.sender_id:
            user = self._require_user(creator_id)

            if user.role not in (Role.ADMIN, Role.MANAGER):
                raise AuthorizationError("Only the sender or a manager can create tasks.")

        if not title.strip():
            raise ValidationError("Task title cannot be empty.")

        if due_at.tzinfo is None:
            raise ValidationError("Due date must include a timezone.")

        if due_at <= self._now():
            raise ValidationError("Due date must be in the future.")

        task = ActionItem(
            task_id=self._id(),
            message_id=message_id,
            title=title.strip(),
            owner_id=owner_id,
            due_at=due_at
        )

        self.tasks[task.task_id] = task

        self.notifications[owner_id].append({
            "task_id": task.task_id,
            "type": "ACTION_ITEM_ASSIGNED",
            "title": task.title
        })

        self._audit(creator_id, "TASK_CREATED", task.task_id)
        return task

    def update_task(
        self,
        actor_id: str,
        task_id: str,
        new_status: TaskStatus
    ):
        self._require_user(actor_id)
        task = self.tasks.get(task_id)

        if task is None:
            raise ValidationError("Task not found.")

        message = self.messages[task.message_id]

        if actor_id != task.owner_id and actor_id != message.sender_id:
            actor = self._require_user(actor_id)

            if actor.role not in (Role.ADMIN, Role.MANAGER):
                raise AuthorizationError("Cannot update this task.")

        allowed = {
            TaskStatus.OPEN: {
                TaskStatus.IN_PROGRESS,
                TaskStatus.BLOCKED,
                TaskStatus.COMPLETED
            },
            TaskStatus.IN_PROGRESS: {
                TaskStatus.BLOCKED,
                TaskStatus.COMPLETED,
                TaskStatus.OPEN
            },
            TaskStatus.BLOCKED: {
                TaskStatus.IN_PROGRESS,
                TaskStatus.OPEN
            },
            TaskStatus.COMPLETED: set()
        }

        if new_status != task.status and new_status not in allowed[task.status]:
            raise ValidationError("Invalid task state transition.")

        task.status = new_status
        self._audit(actor_id, "TASK_STATUS_CHANGED", task_id)

    def overdue_tasks(self, reference_time: Optional[datetime] = None):
        reference_time = reference_time or self._now()

        return [
            task for task in self.tasks.values()
            if task.due_at < reference_time
            and task.status not in (TaskStatus.COMPLETED,)
        ]

    def escalation_report(self):
        now = self._now()
        report = []

        for message in self.messages.values():
            if message.priority not in (
                MessagePriority.HIGH,
                MessagePriority.URGENT
            ):
                continue

            if message.status in (
                MessageStatus.RESOLVED,
                MessageStatus.ARCHIVED
            ):
                continue

            threshold = (
                timedelta(minutes=15)
                if message.priority == MessagePriority.URGENT
                else timedelta(hours=4)
            )

            if now - message.created_at > threshold:
                pending = message.recipients - message.acknowledged_by

                if pending:
                    report.append({
                        "message_id": message.message_id,
                        "priority": message.priority.name,
                        "pending_recipients": sorted(pending),
                        "age_minutes": int(
                            (now - message.created_at).total_seconds() / 60
                        )
                    })

        return report

    def channel_report(self, channel_id: str, viewer_id: str):
        self._require_membership(viewer_id, channel_id)

        channel_messages = [
            message for message in self.messages.values()
            if message.channel_id == channel_id
        ]

        total = len(channel_messages)
        acknowledged = sum(
            message.status == MessageStatus.ACKNOWLEDGED
            for message in channel_messages
        )

        return {
            "channel": self.channels[channel_id].name,
            "total_messages": total,
            "acknowledged_messages": acknowledged,
            "pending_messages": total - acknowledged,
            "tasks": sum(
                task.message_id in {
                    m.message_id for m in channel_messages
                }
                for task in self.tasks.values()
            )
        }

    def export_channel(
        self,
        channel_id: str,
        requester_id: str,
        destination: Path
    ):
        self._require_membership(requester_id, channel_id)

        messages = [
            message for message in self.messages.values()
            if message.channel_id == channel_id
        ]

        data = {
            "channel": asdict(self.channels[channel_id]),
            "messages": [
                {
                    "message_id": m.message_id,
                    "sender_id": m.sender_id,
                    "content": m.content,
                    "priority": m.priority.name,
                    "status": m.status.value,
                    "created_at": m.created_at.isoformat(),
                    "read_by": sorted(m.read_by),
                    "acknowledged_by": sorted(m.acknowledged_by)
                }
                for m in messages
            ]
        }

        destination.parent.mkdir(parents=True, exist_ok=True)

        with destination.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

        self._audit(requester_id, "CHANNEL_EXPORTED", channel_id)


def run_tests():
    system = TeamCommunicationSystem()

    manager = system.register_user(
        "Project Manager", "manager@example.com", Role.MANAGER
    )
    developer = system.register_user(
        "Developer", "developer@example.com", Role.MEMBER
    )
    analyst = system.register_user(
        "Analyst", "analyst@example.com", Role.MEMBER
    )
    observer = system.register_user(
        "Observer", "observer@example.com", Role.OBSERVER
    )

    channel = system.create_channel(
        manager.user_id,
        "Project Phoenix",
        ChannelType.PROJECT,
        {developer.user_id, analyst.user_id}
    )

    message = system.send_message(
        manager.user_id,
        channel.channel_id,
        "Complete the API integration and report blockers.",
        MessagePriority.HIGH
    )

    system.mark_read(developer.user_id, message.message_id)

    assert developer.user_id in message.read_by
    assert developer.user_id not in message.acknowledged_by

    system.acknowledge(developer.user_id, message.message_id)
    system.acknowledge(analyst.user_id, message.message_id)

    assert message.status == MessageStatus.ACKNOWLEDGED

    task = system.create_action_item(
        manager.user_id,
        message.message_id,
        "Complete API integration",
        developer.user_id,
        datetime.now(timezone.utc) + timedelta(days=2)
    )

    system.update_task(
        developer.user_id,
        task.task_id,
        TaskStatus.IN_PROGRESS
    )

    assert task.status == TaskStatus.IN_PROGRESS

    try:
        system.send_message(
            observer.user_id,
            channel.channel_id,
            "Unauthorized message"
        )
    except AuthorizationError:
        pass
    else:
        raise AssertionError("Observer authorization test failed.")

    try:
        system.send_message(
            developer.user_id,
            channel.channel_id,
            "Message to an external recipient",
            recipients={"unknown-user"}
        )
    except AuthorizationError:
        pass
    else:
        raise AssertionError("Recipient validation test failed.")

    assert not system.overdue_tasks()

    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "communication_export.json"
        system.export_channel(
            channel.channel_id,
            manager.user_id,
            output
        )
        assert output.exists()

        exported = json.loads(output.read_text(encoding="utf-8"))
        assert len(exported["messages"]) == 1

    print("All communication workflow tests passed.")
    print(json.dumps(
        system.channel_report(channel.channel_id, manager.user_id),
        indent=2
    ))
    print("Audit events:", len(system.audit_log))


if __name__ == "__main__":
    run_tests()
