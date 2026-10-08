'use strict';

/*
 * Critical Path Method in JavaScript
 *
 * This implementation models a project as an event-driven scheduling
 * system. It demonstrates:
 *
 * - activity dependencies
 * - forward and backward CPM passes
 * - earliest/latest dates
 * - total float
 * - critical activity detection
 * - critical path reconstruction
 * - status checks
 * - event-driven activity updates
 * - delay simulation
 * - validation of cycles and invalid dependencies
 *
 * The program uses only standard JavaScript and runs under Node.js.
 */

class Activity {
    constructor(id, name, duration, predecessors = []) {
        if (!id || !id.trim()) {
            throw new Error('Activity ID is required.');
        }

        if (!name || !name.trim()) {
            throw new Error(`Activity ${id} must have a name.`);
        }

        if (!Number.isFinite(duration) || duration < 0) {
            throw new Error(
                `Activity ${id} must have a non-negative finite duration.`
            );
        }

        if (!Array.isArray(predecessors)) {
            throw new Error(`Predecessors for ${id} must be an array.`);
        }

        if (new Set(predecessors).size !== predecessors.length) {
            throw new Error(
                `Activity ${id} contains duplicate predecessors.`
            );
        }

        this.id = id;
        this.name = name;
        this.duration = duration;
        this.predecessors = [...predecessors];
    }
}

class ProjectEventBus {
    constructor() {
        this.listeners = new Map();
    }

    on(eventName, listener) {
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, []);
        }

        this.listeners.get(eventName).push(listener);
    }

    emit(eventName, payload) {
        const listeners = this.listeners.get(eventName) || [];

        for (const listener of listeners) {
            listener(payload);
        }
    }
}

class CriticalPathEngine {
    constructor(activities) {
        this.activities = new Map();

        for (const activity of activities) {
            if (this.activities.has(activity.id)) {
                throw new Error(
                    `Duplicate activity ID: ${activity.id}`
                );
            }

            this.activities.set(activity.id, activity);
        }

        this.successors = new Map();

        for (const id of this.activities.keys()) {
            this.successors.set(id, []);
        }

        for (const activity of this.activities.values()) {
            for (const predecessor of activity.predecessors) {
                if (!this.activities.has(predecessor)) {
                    throw new Error(
                        `Activity ${activity.id} references unknown ` +
                        `predecessor ${predecessor}.`
                    );
                }

                this.successors.get(predecessor).push(activity.id);
            }
        }

        this.order = this.topologicalSort();
        this.schedule = new Map();
    }

    topologicalSort() {
        const indegree = new Map();

        for (const id of this.activities.keys()) {
            indegree.set(id, 0);
        }

        for (const activity of this.activities.values()) {
            for (const predecessor of activity.predecessors) {
                indegree.set(
                    activity.id,
                    indegree.get(activity.id) + 1
                );
            }
        }

        const queue = [];

        for (const [id, degree] of indegree) {
            if (degree === 0) {
                queue.push(id);
            }
        }

        const order = [];

        while (queue.length > 0) {
            const current = queue.shift();
            order.push(current);

            for (const successor of this.successors.get(current)) {
                indegree.set(
                    successor,
                    indegree.get(successor) - 1
                );

                if (indegree.get(successor) === 0) {
                    queue.push(successor);
                }
            }
        }

        if (order.length !== this.activities.size) {
            throw new Error(
                'The project contains a circular dependency.'
            );
        }

        return order;
    }

    calculate() {
        const schedule = new Map();

        // Forward pass: determine the earliest feasible start and finish.
        for (const id of this.order) {
            const activity = this.activities.get(id);

            const earliestStart = activity.predecessors.length === 0
                ? 0
                : Math.max(
                    ...activity.predecessors.map(
                        predecessor =>
                            schedule.get(predecessor).earliestFinish
                    )
                );

            const earliestFinish =
                earliestStart + activity.duration;

            schedule.set(id, {
                activity,
                earliestStart,
                earliestFinish,
                latestStart: 0,
                latestFinish: 0,
                totalFloat: 0
            });
        }

        const projectDuration = Math.max(
            ...Array.from(schedule.values()).map(
                entry => entry.earliestFinish
            )
        );

        // Backward pass: determine how late an activity can finish without
        // extending the current project completion date.
        for (let index = this.order.length - 1; index >= 0; index--) {
            const id = this.order[index];
            const entry = schedule.get(id);
            const successors = this.successors.get(id);

            const latestFinish = successors.length === 0
                ? projectDuration
                : Math.min(
                    ...successors.map(
                        successor =>
                            schedule.get(successor).latestStart
                    )
                );

            const latestStart =
                latestFinish - entry.activity.duration;

            const totalFloat =
                latestStart - entry.earliestStart;

            entry.latestFinish = latestFinish;
            entry.latestStart = latestStart;
            entry.totalFloat = Math.max(0, totalFloat);
        }

        this.schedule = schedule;

        return schedule;
    }

    get projectDuration() {
        if (this.schedule.size === 0) {
            this.calculate();
        }

        return Math.max(
            ...Array.from(this.schedule.values()).map(
                entry => entry.earliestFinish
            )
        );
    }

    getCriticalActivities() {
        if (this.schedule.size === 0) {
            this.calculate();
        }

        return this.order
            .map(id => this.schedule.get(id))
            .filter(entry => Math.abs(entry.totalFloat) < 1e-9);
    }

    getCriticalPaths() {
        if (this.schedule.size === 0) {
            this.calculate();
        }

        const critical = new Set(
            this.getCriticalActivities().map(
                entry => entry.activity.id
            )
        );

        const starts = this.order.filter(id => {
            if (!critical.has(id)) {
                return false;
            }

            return !this.activities.get(id).predecessors.some(
                predecessor => critical.has(predecessor)
            );
        });

        const paths = [];

        const walk = path => {
            const current = path[path.length - 1];

            const next = this.successors
                .get(current)
                .filter(successor => {
                    if (!critical.has(successor)) {
                        return false;
                    }

                    const currentEntry = this.schedule.get(current);
                    const successorEntry = this.schedule.get(successor);

                    return Math.abs(
                        successorEntry.earliestStart -
                        currentEntry.earliestFinish
                    ) < 1e-9;
                });

            if (next.length === 0) {
                paths.push([...path]);
                return;
            }

            for (const successor of next) {
                walk([...path, successor]);
            }
        };

        for (const start of starts) {
            walk([start]);
        }

        return paths;
    }

    simulateDelay(activityId, delay) {
        if (!this.activities.has(activityId)) {
            throw new Error(`Unknown activity: ${activityId}`);
        }

        if (!Number.isFinite(delay) || delay < 0) {
            throw new Error('Delay must be a non-negative finite number.');
        }

        const modifiedActivities = Array.from(
            this.activities.values()
        ).map(activity => {
            if (activity.id !== activityId) {
                return new Activity(
                    activity.id,
                    activity.name,
                    activity.duration,
                    activity.predecessors
                );
            }

            return new Activity(
                activity.id,
                activity.name,
                activity.duration + delay,
                activity.predecessors
            );
        });

        const simulation = new CriticalPathEngine(
            modifiedActivities
        );

        simulation.calculate();

        return simulation.projectDuration;
    }

    printSchedule() {
        if (this.schedule.size === 0) {
            this.calculate();
        }

        console.log('\nCRITICAL PATH SCHEDULE');
        console.log('='.repeat(108));

        console.log(
            'ID'.padEnd(8) +
            'Activity'.padEnd(31) +
            'Dur'.padStart(8) +
            'ES'.padStart(8) +
            'EF'.padStart(8) +
            'LS'.padStart(8) +
            'LF'.padStart(8) +
            'Float'.padStart(10) +
            'Status'.padStart(15)
        );

        console.log('-'.repeat(108));

        for (const id of this.order) {
            const entry = this.schedule.get(id);

            console.log(
                id.padEnd(8) +
                entry.activity.name.slice(0, 30).padEnd(31) +
                entry.activity.duration.toFixed(1).padStart(8) +
                entry.earliestStart.toFixed(1).padStart(8) +
                entry.earliestFinish.toFixed(1).padStart(8) +
                entry.latestStart.toFixed(1).padStart(8) +
                entry.latestFinish.toFixed(1).padStart(8) +
                entry.totalFloat.toFixed(1).padStart(10) +
                (Math.abs(entry.totalFloat) < 1e-9
                    ? 'CRITICAL'
                    : 'NON-CRITICAL').padStart(15)
            );
        }

        console.log('-'.repeat(108));
        console.log(
            `Project duration: ${this.projectDuration}`
        );

        console.log('\nCritical path(s):');

        for (const path of this.getCriticalPaths()) {
            console.log(
                '  ' +
                path
                    .map(id => `${id}(${this.activities.get(id).name})`)
                    .join(' -> ')
            );
        }
    }
}

function buildReleaseProject() {
    return new CriticalPathEngine([
        new Activity(
            'A',
            'Requirements approval',
            3
        ),
        new Activity(
            'B',
            'Architecture design',
            4,
            ['A']
        ),
        new Activity(
            'C',
            'Database implementation',
            5,
            ['B']
        ),
        new Activity(
            'D',
            'Backend implementation',
            7,
            ['B']
        ),
        new Activity(
            'E',
            'Frontend implementation',
            6,
            ['B']
        ),
        new Activity(
            'F',
            'Integration',
            3,
            ['C', 'D', 'E']
        ),
        new Activity(
            'G',
            'System testing',
            5,
            ['F']
        ),
        new Activity(
            'H',
            'Security validation',
            3,
            ['F']
        ),
        new Activity(
            'I',
            'Operations readiness',
            2,
            ['B']
        ),
        new Activity(
            'J',
            'Production release',
            2,
            ['G', 'H', 'I']
        )
    ]);
}

function demonstrateEventDrivenScheduling(project) {
    /*
     * JavaScript's event model is useful when a scheduling application must
     * react to activity updates. Here an activity duration change triggers
     * recalculation and emits an event for dependent consumers.
     */
    const eventBus = new ProjectEventBus();

    eventBus.on('scheduleCalculated', payload => {
        console.log(
            `\nEVENT: schedule recalculated; ` +
            `project duration = ${payload.duration}`
        );
    });

    eventBus.on('activityDelayed', payload => {
        console.log(
            `EVENT: ${payload.activityId} delayed by ` +
            `${payload.delay}; new project duration = ` +
            `${payload.newDuration}`
        );
    });

    project.calculate();

    eventBus.emit('scheduleCalculated', {
        duration: project.projectDuration
    });

    const activityId = 'D';
    const delay = 2;

    const newDuration = project.simulateDelay(
        activityId,
        delay
    );

    eventBus.emit('activityDelayed', {
        activityId,
        delay,
        newDuration
    });
}

function demonstrateCriticalityAndFloat(project) {
    console.log('\nCRITICALITY AND FLOAT');
    console.log('='.repeat(70));

    const baseline = project.projectDuration;

    for (const id of project.order) {
        const entry = project.schedule.get(id);
        const oneUnitDelay = project.simulateDelay(id, 1);
        const projectImpact = oneUnitDelay - baseline;

        console.log(
            `${id} | ${entry.activity.name} | ` +
            `float=${entry.totalFloat} | ` +
            `+1 duration impact=${projectImpact}`
        );
    }
}

function demonstrateValidation() {
    console.log('\nVALIDATION EXAMPLES');
    console.log('='.repeat(70));

    try {
        new CriticalPathEngine([
            new Activity('A', 'Requirements', 2),
            new Activity('B', 'Implementation', 3, ['MISSING'])
        ]);
    } catch (error) {
        console.log(
            `Invalid dependency rejected: ${error.message}`
        );
    }

    try {
        new CriticalPathEngine([
            new Activity('A', 'First', 2, ['B']),
            new Activity('B', 'Second', 3, ['A'])
        ]);
    } catch (error) {
        console.log(
            `Circular dependency rejected: ${error.message}`
        );
    }
}

function main() {
    console.log('CRITICAL PATH METHOD');
    console.log('Understanding Critical Activities');

    const project = buildReleaseProject();

    project.calculate();
    project.printSchedule();

    demonstrateCriticalityAndFloat(project);
    demonstrateEventDrivenScheduling(project);
    demonstrateValidation();

    console.log('\nINTERPRETATION');
    console.log(
        'A critical activity currently has zero total float and therefore ' +
        'lies on a schedule-controlling path.'
    );
    console.log(
        'Float is dynamic. Changing durations or dependencies can move ' +
        'criticality from one activity or path to another.'
    );
    console.log(
        'A delay to a non-critical activity can be absorbed while the ' +
        'delay remains within its available float.'
    );
}

main();
