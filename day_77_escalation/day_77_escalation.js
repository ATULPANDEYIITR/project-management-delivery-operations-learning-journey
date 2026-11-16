'use strict';

/*
 * Escalation and Critical Problem Reporting Engine
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only.
 *
 * Uses event-driven incident processing, asynchronous notifications,
 * policy evaluation, deduplication and immutable notification records.
 */

const { randomUUID } = require('node:crypto');
const fs = require('node:fs/promises');
const EventEmitter = require('node:events');

const Severity = Object.freeze({
    LOW: 'LOW',
    MEDIUM: 'MEDIUM',
    HIGH: 'HIGH',
    CRITICAL: 'CRITICAL'
});

const Status = Object.freeze({
    REPORTED: 'REPORTED',
    ACKNOWLEDGED: 'ACKNOWLEDGED',
    INVESTIGATING: 'INVESTIGATING',
    ESCALATED: 'ESCALATED',
    RESOLVED: 'RESOLVED',
    CLOSED: 'CLOSED'
});

const Level = Object.freeze({
    L1: 1,
    L2: 2,
    L3: 3,
    EXECUTIVE: 4
});

const POLICIES = Object.freeze({
    LOW: Object.freeze({
        acknowledgementMinutes: 480,
        resolutionMinutes: 2880,
        level: Level.L1
    }),
    MEDIUM: Object.freeze({
        acknowledgementMinutes: 120,
        resolutionMinutes: 1440,
        level: Level.L1
    }),
    HIGH: Object.freeze({
        acknowledgementMinutes: 30,
        resolutionMinutes: 240,
        level: Level.L2
    }),
    CRITICAL: Object.freeze({
        acknowledgementMinutes: 10,
        resolutionMinutes: 60,
        level: Level.EXECUTIVE
    })
});

const TRANSITIONS = Object.freeze({
    REPORTED: [Status.ACKNOWLEDGED, Status.ESCALATED],
    ACKNOWLEDGED: [Status.INVESTIGATING, Status.ESCALATED],
    INVESTIGATING: [Status.ESCALATED, Status.RESOLVED],
    ESCALATED: [
        Status.ACKNOWLEDGED,
        Status.INVESTIGATING,
        Status.RESOLVED
    ],
    RESOLVED: [Status.CLOSED, Status.INVESTIGATING],
    CLOSED: []
});

class DomainError extends Error {
    constructor(message, code = 'DOMAIN_ERROR') {
        super(message);
        this.name = 'DomainError';
        this.code = code;
    }
}

function validateText(value, field, maximum) {
    if (typeof value !== 'string') {
        throw new DomainError(`${field} must be a string.`);
    }

    const normalized = value.trim();

    if (!normalized || normalized.length > maximum) {
        throw new DomainError(
            `${field} must contain 1 to ${maximum} characters.`
        );
    }

    return normalized;
}

function minutesFromNow(minutes) {
    return new Date(Date.now() + minutes * 60_000).toISOString();
}

function canManage(actor, severity) {
    if (!actor) return false;

    if (['administrator', 'incident_manager'].includes(actor.role)) {
        return true;
    }

    if (actor.role === 'team_lead') {
        return severity !== Severity.CRITICAL;
    }

    return actor.role === 'responder';
}

class Incident {
    constructor(data) {
        this.id = randomUUID();
        this.title = data.title;
        this.description = data.description;
        this.category = data.category;
        this.severity = data.severity;
        this.department = data.department;
        this.reporterId = data.reporterId;
        this.reportedAt = new Date().toISOString();

        const policy = POLICIES[data.severity];

        this.acknowledgementDeadline = minutesFromNow(
            policy.acknowledgementMinutes
        );

        this.resolutionDeadline = minutesFromNow(
            policy.resolutionMinutes
        );

        this.status = Status.REPORTED;
        this.escalationLevel = policy.level;
        this.assignedTo = null;
        this.acknowledgedAt = null;
        this.resolvedAt = null;
        this.resolutionNotes = null;
        this.parentIncidentId = data.parentIncidentId || null;
        this.tags = new Set(data.tags || []);
        this.audit = [];
        this.version = 1;
    }

    snapshot() {
        return Object.freeze({
            id: this.id,
            title: this.title,
            description: this.description,
            category: this.category,
            severity: this.severity,
            department: this.department,
            reporterId: this.reporterId,
            reportedAt: this.reportedAt,
            acknowledgementDeadline: this.acknowledgementDeadline,
            resolutionDeadline: this.resolutionDeadline,
            status: this.status,
            escalationLevel: this.escalationLevel,
            assignedTo: this.assignedTo,
            acknowledgedAt: this.acknowledgedAt,
            resolvedAt: this.resolvedAt,
            resolutionNotes: this.resolutionNotes,
            tags: [...this.tags],
            version: this.version
        });
    }
}

class NotificationService {
    constructor() {
        this.queue = [];
        this.processedKeys = new Set();
    }

    async send(notification) {
        const key = notification.idempotencyKey;

        if (key && this.processedKeys.has(key)) {
            return { duplicate: true };
        }

        // A real transport adapter can replace this in-memory delivery.
        const delivered = Object.freeze({
            ...notification,
            deliveryStatus: 'DELIVERED',
            deliveredAt: new Date().toISOString()
        });

        if (key) this.processedKeys.add(key);

        this.queue.push(delivered);

        return delivered;
    }

    async dispatchBatch(notifications) {
        const results = await Promise.allSettled(
            notifications.map(item => this.send(item))
        );

        return results.map(result => ({
            success: result.status === 'fulfilled',
            result: result.status === 'fulfilled'
                ? result.value
                : result.reason.message
        }));
    }
}

class EscalationEngine extends EventEmitter {
    constructor() {
        super();

        this.incidents = new Map();
        this.actors = new Map();
        this.idempotencyKeys = new Set();
        this.notifications = new NotificationService();
        this.eventHistory = [];
    }

    registerActor(actor) {
        const id = validateText(actor.id, 'Actor ID', 80);

        if (this.actors.has(id)) {
            throw new DomainError('Actor already registered.');
        }

        const validRoles = [
            'reporter',
            'responder',
            'team_lead',
            'incident_manager',
            'administrator'
        ];

        if (!validRoles.includes(actor.role)) {
            throw new DomainError('Invalid actor role.');
        }

        this.actors.set(id, Object.freeze({
            id,
            name: validateText(actor.name, 'Actor name', 120),
            role: actor.role,
            department: validateText(
                actor.department,
                'Department',
                100
            )
        }));
    }

    actor(id) {
        const actor = this.actors.get(id);

        if (!actor) {
            throw new DomainError('Actor not found.', 'ACTOR_NOT_FOUND');
        }

        return actor;
    }

    incident(id) {
        const incident = this.incidents.get(id);

        if (!incident) {
            throw new DomainError(
                'Incident not found.',
                'INCIDENT_NOT_FOUND'
            );
        }

        return incident;
    }

    authorize(actorId, incident) {
        const actor = this.actor(actorId);

        if (!canManage(actor, incident.severity)) {
            throw new DomainError(
                'Insufficient permission for this operation.',
                'FORBIDDEN'
            );
        }

        return actor;
    }

    record(incident, actorId, action, details) {
        const event = Object.freeze({
            eventId: randomUUID(),
            incidentId: incident.id,
            actorId,
            action,
            details,
            timestamp: new Date().toISOString()
        });

        incident.audit.push(event);
        incident.version++;

        this.eventHistory.push(event);
        this.emit('incidentEvent', event);

        return event;
    }

    async notify(incident, event, recipient) {
        return this.notifications.send({
            id: randomUUID(),
            incidentId: incident.id,
            event,
            recipient,
            createdAt: new Date().toISOString(),
            idempotencyKey: `${incident.id}:${event}:${recipient}`
        });
    }

    async report(data) {
        this.actor(data.reporterId);

        if (!Object.hasOwn(POLICIES, data.severity)) {
            throw new DomainError('Unsupported severity.');
        }

        if (data.idempotencyKey) {
            if (this.idempotencyKeys.has(data.idempotencyKey)) {
                throw new DomainError('Duplicate report request.');
            }
        }

        const normalized = {
            title: validateText(data.title, 'Title', 160),
            description: validateText(
                data.description,
                'Description',
                5000
            ),
            category: validateText(data.category, 'Category', 80),
            department: validateText(
                data.department,
                'Department',
                100
            ),
            reporterId: data.reporterId,
            severity: data.severity,
            tags: data.tags || [],
            parentIncidentId: data.parentIncidentId || null
        };

        if (normalized.parentIncidentId) {
            this.incident(normalized.parentIncidentId);
        }

        if (normalized.tags.some(tag => (
            typeof tag !== 'string' || tag.length > 60
        ))) {
            throw new DomainError('Invalid incident tag.');
        }

        const incident = new Incident(normalized);

        this.incidents.set(incident.id, incident);

        if (data.idempotencyKey) {
            this.idempotencyKeys.add(data.idempotencyKey);
        }

        this.record(
            incident,
            data.reporterId,
            'REPORTED',
            `Severity ${data.severity}`
        );

        await this.notify(
            incident,
            'INCIDENT_REPORTED',
            'incident_management'
        );

        if (data.severity === Severity.CRITICAL) {
            await this.notify(
                incident,
                'CRITICAL_ALERT',
                'executive_team'
            );
        }

        return incident.snapshot();
    }

    transition(incident, actorId, newStatus, details) {
        if (!TRANSITIONS[incident.status].includes(newStatus)) {
            throw new DomainError(
                `Invalid transition: ${incident.status} -> ${newStatus}`
            );
        }

        const previous = incident.status;
        incident.status = newStatus;

        this.record(
            incident,
            actorId,
            'STATUS_CHANGED',
            `${previous} -> ${newStatus}: ${details}`
        );
    }

    async assign(incidentId, actorId, assigneeId) {
        const incident = this.incident(incidentId);
        this.authorize(actorId, incident);

        this.actor(assigneeId);

        incident.assignedTo = assigneeId;

        this.record(
            incident,
            actorId,
            'ASSIGNED',
            `Assigned to ${assigneeId}`
        );

        await this.notify(
            incident,
            'INCIDENT_ASSIGNED',
            assigneeId
        );
    }

    async acknowledge(incidentId, actorId) {
        const incident = this.incident(incidentId);
        this.authorize(actorId, incident);

        this.transition(
            incident,
            actorId,
            Status.ACKNOWLEDGED,
            'Incident acknowledged'
        );

        incident.acknowledgedAt = new Date().toISOString();

        await this.notify(
            incident,
            'INCIDENT_ACKNOWLEDGED',
            incident.reporterId
        );
    }

    investigate(incidentId, actorId) {
        const incident = this.incident(incidentId);
        this.authorize(actorId, incident);

        if (!incident.assignedTo) {
            throw new DomainError(
                'An incident must have an owner before investigation.'
            );
        }

        this.transition(
            incident,
            actorId,
            Status.INVESTIGATING,
            'Investigation started'
        );
    }

    async escalate(incidentId, actorId, reason, targetLevel) {
        const incident = this.incident(incidentId);
        this.authorize(actorId, incident);

        reason = validateText(reason, 'Escalation reason', 1000);

        if ([Status.RESOLVED, Status.CLOSED].includes(incident.status)) {
            throw new DomainError('Cannot escalate a completed incident.');
        }

        const nextLevel = targetLevel ??
            Math.min(incident.escalationLevel + 1, Level.EXECUTIVE);

        if (
            !Number.isInteger(nextLevel) ||
            nextLevel <= incident.escalationLevel ||
            nextLevel > Level.EXECUTIVE
        ) {
            throw new DomainError('Invalid escalation level.');
        }

        incident.escalationLevel = nextLevel;

        if (incident.status !== Status.ESCALATED) {
            this.transition(
                incident,
                actorId,
                Status.ESCALATED,
                reason
            );
        } else {
            this.record(
                incident,
                actorId,
                'ESCALATED_AGAIN',
                reason
            );
        }

        const recipient = nextLevel === Level.EXECUTIVE
            ? 'executive_team'
            : `management_level_${nextLevel}`;

        await this.notify(
            incident,
            'INCIDENT_ESCALATED',
            recipient
        );
    }

    async resolve(incidentId, actorId, notes) {
        const incident = this.incident(incidentId);
        this.authorize(actorId, incident);

        notes = validateText(notes, 'Resolution notes', 3000);

        this.transition(
            incident,
            actorId,
            Status.RESOLVED,
            notes
        );

        incident.resolvedAt = new Date().toISOString();
        incident.resolutionNotes = notes;

        await this.notify(
            incident,
            'INCIDENT_RESOLVED',
            incident.reporterId
        );
    }

    close(incidentId, actorId) {
        const incident = this.incident(incidentId);
        this.authorize(actorId, incident);

        if (!incident.resolutionNotes) {
            throw new DomainError('Resolution evidence is required.');
        }

        this.transition(
            incident,
            actorId,
            Status.CLOSED,
            'Administrative closure'
        );
    }

    reopen(incidentId, actorId, reason) {
        const incident = this.incident(incidentId);
        this.authorize(actorId, incident);

        reason = validateText(reason, 'Reopening reason', 1000);

        this.transition(
            incident,
            actorId,
            Status.INVESTIGATING,
            reason
        );

        incident.resolvedAt = null;
        incident.resolutionNotes = null;
    }

    evaluateDeadlines(now = new Date()) {
        const breaches = [];

        for (const incident of this.incidents.values()) {
            if (
                [Status.RESOLVED, Status.CLOSED].includes(incident.status)
            ) {
                continue;
            }

            const acknowledgementLate =
                !incident.acknowledgedAt &&
                now > new Date(incident.acknowledgementDeadline);

            const resolutionLate =
                now > new Date(incident.resolutionDeadline);

            if (acknowledgementLate || resolutionLate) {
                const type = acknowledgementLate
                    ? 'ACKNOWLEDGEMENT_BREACH'
                    : 'RESOLUTION_BREACH';

                breaches.push({
                    incidentId: incident.id,
                    type,
                    severity: incident.severity
                });
            }
        }

        return breaches;
    }

    dashboard() {
        const summary = {
            total: this.incidents.size,
            open: 0,
            resolved: 0,
            critical: 0,
            escalated: 0,
            bySeverity: {},
            byStatus: {}
        };

        for (const incident of this.incidents.values()) {
            summary.bySeverity[incident.severity] =
                (summary.bySeverity[incident.severity] || 0) + 1;

            summary.byStatus[incident.status] =
                (summary.byStatus[incident.status] || 0) + 1;

            if (
                ![Status.RESOLVED, Status.CLOSED].includes(incident.status)
            ) {
                summary.open++;
            } else {
                summary.resolved++;
            }

            if (incident.severity === Severity.CRITICAL) {
                summary.critical++;
            }

            if (incident.status === Status.ESCALATED) {
                summary.escalated++;
            }
        }

        return summary;
    }

    async exportReport(filename) {
        const records = [...this.incidents.values()]
            .map(incident => incident.snapshot());

        const output = JSON.stringify({
            generatedAt: new Date().toISOString(),
            dashboard: this.dashboard(),
            incidents: records,
            auditEvents: this.eventHistory
        }, null, 2);

        await fs.writeFile(filename, output, {
            encoding: 'utf8',
            flag: 'w',
            mode: 0o600
        });
    }
}

async function main() {
    const engine = new EscalationEngine();

    engine.on('incidentEvent', event => {
        console.log(
            `[EVENT] ${event.action}: ${event.incidentId}`
        );
    });

    engine.registerActor({
        id: 'U001',
        name: 'Operations Reporter',
        role: 'reporter',
        department: 'Operations'
    });

    engine.registerActor({
        id: 'U002',
        name: 'Technical Responder',
        role: 'responder',
        department: 'Technology'
    });

    engine.registerActor({
        id: 'U003',
        name: 'Incident Manager',
        role: 'incident_manager',
        department: 'Operations'
    });

    engine.registerActor({
        id: 'U004',
        name: 'Executive Director',
        role: 'administrator',
        department: 'Executive'
    });

    const incident = await engine.report({
        reporterId: 'U001',
        title: 'Critical payment processing failure',
        description: 'Production payment requests are failing.',
        category: 'Financial Infrastructure',
        severity: Severity.CRITICAL,
        department: 'Technology',
        idempotencyKey: 'PAYMENT-FAILURE-001',
        tags: ['payments', 'production', 'availability']
    });

    await engine.assign(incident.id, 'U003', 'U002');
    await engine.acknowledge(incident.id, 'U003');

    engine.investigate(incident.id, 'U002');

    await engine.escalate(
        incident.id,
        'U003',
        'Customer payment processing is unavailable.',
        Level.EXECUTIVE
    );

    await engine.resolve(
        incident.id,
        'U003',
        'Payment gateway restored and test transactions passed.'
    );

    engine.close(incident.id, 'U003');

    const report = {
        dashboard: engine.dashboard(),
        deadlineBreaches: engine.evaluateDeadlines(),
        notifications: engine.notifications.queue
    };

    console.log('\nREPORT');
    console.log(JSON.stringify(report, null, 2));

    await engine.exportReport('escalation_report.json');

    try {
        engine.investigate(incident.id, 'U002');
    } catch (error) {
        console.log('\nExpected failure:', error.message);
    }

    console.log('\nExport completed: escalation_report.json');
}

main().catch(error => {
    console.error('Fatal application error:', error.message);
    process.exitCode = 1;
});
