"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs/promises");

const Role = Object.freeze({
    ADMIN: "ADMIN",
    MANAGER: "MANAGER",
    MEMBER: "MEMBER",
    OBSERVER: "OBSERVER"
});

const ChannelType = Object.freeze({
    GENERAL: "GENERAL",
    PROJECT: "PROJECT",
    ANNOUNCEMENTS: "ANNOUNCEMENTS",
    INCIDENT: "INCIDENT",
    PRIVATE: "PRIVATE"
});

const Priority = Object.freeze({
    LOW: 1,
    NORMAL: 2,
    HIGH: 3,
    URGENT: 4
});

const TaskState = Object.freeze({
    OPEN: "OPEN",
    IN_PROGRESS: "IN_PROGRESS",
    BLOCKED: "BLOCKED",
    COMPLETED: "COMPLETED"
});

class CommunicationError extends Error {}
class ValidationError extends CommunicationError {}
class AuthorizationError extends CommunicationError {}
class ConflictError extends CommunicationError {}

function generateId() {
    return crypto.randomUUID();
}

function validateEnum(value, enumeration, label) {
    if (!Object.values(enumeration).includes(value)) {
        throw new ValidationError(`Invalid ${label}: ${value}`);
    }
}

class CommunicationEventBus {
    constructor() {
        this.listeners = new Map();
    }

    on(eventName, listener) {
        if (typeof listener !== "function") {
            throw new ValidationError("Listener must be a function.");
        }

        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, new Set());
        }

        this.listeners.get(eventName).add(listener);

        return () => this.listeners.get(eventName)?.delete(listener);
    }

    async emit(eventName, payload) {
        const listeners = [
            ...(this.listeners.get(eventName) || [])
        ];

        const results = await Promise.allSettled(
            listeners.map(listener => listener(Object.freeze({...payload})))
        );

        return results;
    }
}

class NotificationQueue {
    constructor() {
        this.pending = new Map();
        this.deliveryHistory = [];
    }

    enqueue(userId, notification) {
        if (!this.pending.has(userId)) {
            this.pending.set(userId, []);
        }

        this.pending.get(userId).push({
            ...notification,
            queuedAt: new Date().toISOString()
        });
    }

    async dispatch(userId, deliveryHandler) {
        const queue = this.pending.get(userId) || [];
        const remaining = [];

        for (const notification of queue) {
            try {
                await deliveryHandler(notification);

                this.deliveryHistory.push({
                    userId,
                    notificationId: notification.id,
                    deliveredAt: new Date().toISOString()
                });
            } catch (error) {
                remaining.push(notification);

                this.deliveryHistory.push({
                    userId,
                    notificationId: notification.id,
                    error: error.message,
                    failedAt: new Date().toISOString()
                });
            }
        }

        this.pending.set(userId, remaining);

        return {
            attempted: queue.length,
            delivered: queue.length - remaining.length,
            failed: remaining.length
        };
    }

    getUnreadCount(userId) {
        return (this.pending.get(userId) || []).length;
    }
}

class TeamCommunicationPlatform {
    constructor() {
        this.users = new Map();
        this.channels = new Map();
        this.messages = new Map();
        this.tasks = new Map();
        this.events = new CommunicationEventBus();
        this.notifications = new NotificationQueue();
        this.audit = [];

        this.events.on("message.sent", async message => {
            for (const recipientId of message.recipients) {
                this.notifications.enqueue(recipientId, {
                    id: generateId(),
                    type: "NEW_MESSAGE",
                    messageId: message.id,
                    priority: message.priority
                });
            }
        });

        this.events.on("task.assigned", async task => {
            this.notifications.enqueue(task.ownerId, {
                id: generateId(),
                type: "TASK_ASSIGNED",
                taskId: task.id,
                title: task.title
            });
        });
    }

    auditEvent(actorId, action, targetId) {
        this.audit.push(Object.freeze({
            actorId,
            action,
            targetId,
            timestamp: new Date().toISOString()
        }));
    }

    getUser(userId) {
        const user = this.users.get(userId);

        if (!user || !user.active) {
            throw new AuthorizationError("User is unavailable.");
        }

        return user;
    }

    getChannel(channelId) {
        const channel = this.channels.get(channelId);

        if (!channel || channel.archived) {
            throw new ValidationError("Channel is unavailable.");
        }

        return channel;
    }

    requireMembership(userId, channelId) {
        const user = this.getUser(userId);
        const channel = this.getChannel(channelId);

        if (!channel.members.has(userId)) {
            throw new AuthorizationError("Channel membership required.");
        }

        return {user, channel};
    }

    registerUser(name, email, role = Role.MEMBER) {
        validateEnum(role, Role, "role");

        if (typeof name !== "string" || !name.trim()) {
            throw new ValidationError("Name is required.");
        }

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            throw new ValidationError("Invalid email.");
        }

        const normalizedEmail = email.toLowerCase();

        if ([...this.users.values()].some(
            user => user.email === normalizedEmail
        )) {
            throw new ConflictError("Email already registered.");
        }

        const user = Object.freeze({
            id: generateId(),
            name: name.trim(),
            email: normalizedEmail,
            role,
            active: true
        });

        this.users.set(user.id, user);
        this.auditEvent(user.id, "USER_REGISTERED", user.id);

        return user;
    }

    createChannel(creatorId, name, type, memberIds = []) {
        const creator = this.getUser(creatorId);

        if (![Role.ADMIN, Role.MANAGER].includes(creator.role)) {
            throw new AuthorizationError("Channel creation denied.");
        }

        validateEnum(type, ChannelType, "channel type");

        if (typeof name !== "string" || !name.trim() || name.length > 80) {
            throw new ValidationError("Invalid channel name.");
        }

        const members = new Set([creatorId, ...memberIds]);

        for (const memberId of members) {
            this.getUser(memberId);
        }

        if (type === ChannelType.PRIVATE && members.size < 2) {
            throw new ValidationError(
                "Private channels require multiple members."
            );
        }

        const channel = {
            id: generateId(),
            name: name.trim(),
            type,
            createdBy: creatorId,
            members,
            archived: false,
            createdAt: new Date().toISOString()
        };

        this.channels.set(channel.id, channel);
        this.auditEvent(creatorId, "CHANNEL_CREATED", channel.id);

        return channel;
    }

    addMember(actorId, channelId, memberId) {
        const {user, channel} = this.requireMembership(
            actorId,
            channelId
        );

        this.getUser(memberId);

        if (![Role.ADMIN, Role.MANAGER].includes(user.role)) {
            throw new AuthorizationError("Insufficient permissions.");
        }

        channel.members.add(memberId);
        this.auditEvent(actorId, "MEMBER_ADDED", channelId);
    }

    async sendMessage({
        senderId,
        channelId,
        content,
        priority = Priority.NORMAL,
        recipients,
        parentId = null
    }) {
        const {user, channel} = this.requireMembership(
            senderId,
            channelId
        );

        if (user.role === Role.OBSERVER) {
            throw new AuthorizationError("Observers cannot post.");
        }

        if (channel.type === ChannelType.ANNOUNCEMENTS &&
            ![Role.ADMIN, Role.MANAGER].includes(user.role)) {
            throw new AuthorizationError(
                "Announcement publishing is restricted."
            );
        }

        if (typeof content !== "string" ||
            !content.trim() ||
            content.length > 10000) {
            throw new ValidationError("Invalid message content.");
        }

        if (!Object.values(Priority).includes(priority)) {
            throw new ValidationError("Invalid message priority.");
        }

        if (parentId !== null) {
            const parent = this.messages.get(parentId);

            if (!parent || parent.channelId !== channelId) {
                throw new ValidationError("Invalid reply reference.");
            }
        }

        const targets = new Set(
            recipients === undefined
                ? [...channel.members].filter(id => id !== senderId)
                : recipients
        );

        for (const recipientId of targets) {
            if (!channel.members.has(recipientId)) {
                throw new AuthorizationError(
                    "Recipient must belong to the channel."
                );
            }
        }

        const message = {
            id: generateId(),
            channelId,
            senderId,
            content: content.trim(),
            priority,
            recipients: targets,
            parentId,
            readBy: new Set(),
            acknowledgedBy: new Set(),
            status: "SENT",
            createdAt: new Date().toISOString(),
            editedAt: null
        };

        this.messages.set(message.id, message);
        this.auditEvent(senderId, "MESSAGE_SENT", message.id);

        const eventResults = await this.events.emit(
            "message.sent",
            message
        );

        return {
            message,
            eventFailures: eventResults.filter(
                result => result.status === "rejected"
            ).length
        };
    }

    markRead(userId, messageId) {
        const user = this.getUser(userId);
        const message = this.messages.get(messageId);

        if (!message) {
            throw new ValidationError("Message not found.");
        }

        this.requireMembership(userId, message.channelId);

        if (userId !== message.senderId &&
            !message.recipients.has(userId)) {
            throw new AuthorizationError("Message access denied.");
        }

        message.readBy.add(userId);
        this.auditEvent(userId, "MESSAGE_READ", messageId);
    }

    acknowledge(userId, messageId) {
        this.markRead(userId, messageId);

        const message = this.messages.get(messageId);

        if (!message.recipients.has(userId)) {
            throw new AuthorizationError(
                "Only designated recipients can acknowledge."
            );
        }

        message.acknowledgedBy.add(userId);

        if ([...message.recipients].every(
            id => message.acknowledgedBy.has(id)
        )) {
            message.status = "ACKNOWLEDGED";
        }

        this.auditEvent(userId, "MESSAGE_ACKNOWLEDGED", messageId);
    }

    editMessage(actorId, messageId, newContent) {
        const actor = this.getUser(actorId);
        const message = this.messages.get(messageId);

        if (!message) {
            throw new ValidationError("Message not found.");
        }

        if (actorId !== message.senderId && actor.role !== Role.ADMIN) {
            throw new AuthorizationError("Edit permission denied.");
        }

        if (message.status === "ARCHIVED") {
            throw new ConflictError("Archived messages cannot be edited.");
        }

        if (typeof newContent !== "string" ||
            !newContent.trim() ||
            newContent.length > 10000) {
            throw new ValidationError("Invalid message content.");
        }

        message.content = newContent.trim();
        message.editedAt = new Date().toISOString();

        this.auditEvent(actorId, "MESSAGE_EDITED", messageId);
    }

    async createTask({
        creatorId,
        messageId,
        ownerId,
        title,
        dueAt
    }) {
        const message = this.messages.get(messageId);

        if (!message) {
            throw new ValidationError("Source message not found.");
        }

        this.requireMembership(creatorId, message.channelId);
        this.requireMembership(ownerId, message.channelId);

        const creator = this.getUser(creatorId);

        if (creatorId !== message.senderId &&
            ![Role.ADMIN, Role.MANAGER].includes(creator.role)) {
            throw new AuthorizationError("Task assignment denied.");
        }

        if (typeof title !== "string" || !title.trim()) {
            throw new ValidationError("Task title is required.");
        }

        const dueDate = new Date(dueAt);

        if (Number.isNaN(dueDate.getTime()) ||
            dueDate <= new Date()) {
            throw new ValidationError("Due date must be in the future.");
        }

        const task = {
            id: generateId(),
            messageId,
            ownerId,
            title: title.trim(),
            dueAt: dueDate.toISOString(),
            state: TaskState.OPEN,
            createdAt: new Date().toISOString()
        };

        this.tasks.set(task.id, task);
        this.auditEvent(creatorId, "TASK_CREATED", task.id);

        const results = await this.events.emit("task.assigned", task);

        return {
            task,
            eventFailures: results.filter(
                result => result.status === "rejected"
            ).length
        };
    }

    updateTask(actorId, taskId, nextState) {
        this.getUser(actorId);
        validateEnum(nextState, TaskState, "task state");

        const task = this.tasks.get(taskId);

        if (!task) {
            throw new ValidationError("Task not found.");
        }

        const message = this.messages.get(task.messageId);
        const actor = this.getUser(actorId);

        if (actorId !== task.ownerId &&
            actorId !== message.senderId &&
            ![Role.ADMIN, Role.MANAGER].includes(actor.role)) {
            throw new AuthorizationError("Task update denied.");
        }

        const transitions = {
            OPEN: ["IN_PROGRESS", "BLOCKED", "COMPLETED"],
            IN_PROGRESS: ["OPEN", "BLOCKED", "COMPLETED"],
            BLOCKED: ["OPEN", "IN_PROGRESS"],
            COMPLETED: []
        };

        if (task.state !== nextState &&
            !transitions[task.state].includes(nextState)) {
            throw new ConflictError(
                `Cannot move task from ${task.state} to ${nextState}.`
            );
        }

        task.state = nextState;
        this.auditEvent(actorId, "TASK_UPDATED", taskId);
    }

    getEscalations(now = new Date()) {
        const escalations = [];

        for (const message of this.messages.values()) {
            if (![Priority.HIGH, Priority.URGENT].includes(
                message.priority
            )) {
                continue;
            }

            if (["RESOLVED", "ARCHIVED"].includes(message.status)) {
                continue;
            }

            const age = now - new Date(message.createdAt);
            const threshold = message.priority === Priority.URGENT
                ? 15 * 60 * 1000
                : 4 * 60 * 60 * 1000;

            const pending = [...message.recipients].filter(
                id => !message.acknowledgedBy.has(id)
            );

            if (age > threshold && pending.length > 0) {
                escalations.push({
                    messageId: message.id,
                    priority: message.priority,
                    pendingRecipients: pending,
                    ageMinutes: Math.floor(age / 60000)
                });
            }
        }

        return escalations;
    }

    getChannelAnalytics(viewerId, channelId) {
        this.requireMembership(viewerId, channelId);

        const messages = [...this.messages.values()].filter(
            message => message.channelId === channelId
        );

        const priorities = Object.fromEntries(
            Object.entries(Priority).map(([name, value]) => [
                name,
                messages.filter(message => message.priority === value).length
            ])
        );

        const acknowledged = messages.filter(
            message => message.status === "ACKNOWLEDGED"
        ).length;

        return {
            channelId,
            totalMessages: messages.length,
            acknowledged,
            pending: messages.length - acknowledged,
            acknowledgementRate: messages.length === 0
                ? 0
                : Number((acknowledged / messages.length).toFixed(3)),
            priorities
        };
    }

    async exportChannel(viewerId, channelId, destination) {
        this.requireMembership(viewerId, channelId);

        const channel = this.getChannel(channelId);

        const messages = [...this.messages.values()]
            .filter(message => message.channelId === channelId)
            .map(message => ({
                ...message,
                recipients: [...message.recipients],
                readBy: [...message.readBy],
                acknowledgedBy: [...message.acknowledgedBy]
            }));

        const data = JSON.stringify({
            channel: {
                id: channel.id,
                name: channel.name,
                type: channel.type,
                members: [...channel.members]
            },
            messages
        }, null, 2);

        await fs.writeFile(destination, data, {
            encoding: "utf8",
            flag: "wx",
            mode: 0o600
        });

        this.auditEvent(viewerId, "CHANNEL_EXPORTED", channelId);
    }
}

async function main() {
    const platform = new TeamCommunicationPlatform();

    const manager = platform.registerUser(
        "Project Manager",
        "manager@example.com",
        Role.MANAGER
    );

    const engineer = platform.registerUser(
        "Software Engineer",
        "engineer@example.com",
        Role.MEMBER
    );

    const tester = platform.registerUser(
        "Quality Analyst",
        "tester@example.com",
        Role.MEMBER
    );

    const channel = platform.createChannel(
        manager.id,
        "Product Launch",
        ChannelType.PROJECT,
        [engineer.id, tester.id]
    );

    const {message, eventFailures} = await platform.sendMessage({
        senderId: manager.id,
        channelId: channel.id,
        content: "Complete integration testing before deployment.",
        priority: Priority.HIGH
    });

    platform.markRead(engineer.id, message.id);
    platform.acknowledge(engineer.id, message.id);
    platform.acknowledge(tester.id, message.id);

    const {task} = await platform.createTask({
        creatorId: manager.id,
        messageId: message.id,
        ownerId: engineer.id,
        title: "Complete integration tests",
        dueAt: new Date(Date.now() + 86400000)
    });

    platform.updateTask(engineer.id, task.id, TaskState.IN_PROGRESS);

    const delivery = await platform.notifications.dispatch(
        engineer.id,
        async notification => {
            if (!notification.id) {
                throw new Error("Invalid notification.");
            }
        }
    );

    console.log("Communication analytics:");
    console.log(
        platform.getChannelAnalytics(manager.id, channel.id)
    );

    console.log("Delivery:", delivery);
    console.log("Event failures:", eventFailures);
    console.log("Escalations:", platform.getEscalations());
    console.log("Audit events:", platform.audit.length);

    try {
        platform.updateTask(
            engineer.id,
            task.id,
            TaskState.COMPLETED
        );

        platform.updateTask(
            engineer.id,
            task.id,
            TaskState.IN_PROGRESS
        );
    } catch (error) {
        console.log("Expected state validation:", error.message);
    }

    try {
        await platform.sendMessage({
            senderId: engineer.id,
            channelId: channel.id,
            content: "Unauthorized external delivery",
            recipients: ["unknown-user"]
        });
    } catch (error) {
        console.log("Expected authorization failure:", error.message);
    }

    console.log("Team communication workflow completed.");
}

main().catch(error => {
    console.error("Application failure:", error.message);
    process.exitCode = 1;
});
