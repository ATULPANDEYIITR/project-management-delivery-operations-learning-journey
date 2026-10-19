"use strict";

/*
 * Resource availability is modeled as a stateful system rather than as a
 * collection of unrelated counters. Each resource pool owns its capacity,
 * current availability, and allocations. The manager coordinates requests
 * that may span multiple resource types.
 */

const ResourceType = Object.freeze({
    COMPUTE: "compute",
    MEMORY: "memory",
    STORAGE: "storage",
    DATABASE_CONNECTION: "database_connection",
    API_QUOTA: "api_quota"
});

const JobState = Object.freeze({
    QUEUED: "queued",
    RUNNING: "running",
    COMPLETED: "completed",
    REJECTED: "rejected"
});

class ResourcePool {
    constructor(name, type, capacity) {
        if (!Number.isInteger(capacity) || capacity <= 0) {
            throw new RangeError("Capacity must be a positive integer");
        }

        this.name = name;
        this.type = type;
        this.capacity = capacity;
        this.available = capacity;
        this.allocations = new Map();
    }

    canAllocate(amount) {
        return Number.isInteger(amount) && amount > 0 && amount <= this.available;
    }

    allocate(owner, amount) {
        if (!this.canAllocate(amount)) {
            return false;
        }

        this.available -= amount;
        this.allocations.set(
            owner,
            (this.allocations.get(owner) ?? 0) + amount
        );

        return true;
    }

    release(owner) {
        const amount = this.allocations.get(owner) ?? 0;

        if (amount === 0) {
            return 0;
        }

        this.available += amount;
        this.allocations.delete(owner);
        return amount;
    }

    get utilization() {
        return (this.capacity - this.available) / this.capacity;
    }
}

class ResourceManager {
    constructor() {
        this.pools = new Map();
    }

    addPool(name, type, capacity) {
        if (this.pools.has(type)) {
            throw new Error(`A pool already exists for ${type}`);
        }

        this.pools.set(type, new ResourcePool(name, type, capacity));
    }

    /*
     * JavaScript is single-threaded at the language level, but asynchronous
     * callbacks can interleave operations. The manager therefore performs
     * all availability checks before mutating any pool. This prevents a
     * multi-resource request from partially succeeding.
     */
    request(owner, requirements) {
        if (typeof owner !== "string" || owner.trim() === "") {
            throw new TypeError("Owner must be a non-empty string");
        }

        const combined = new Map();

        for (const requirement of requirements) {
            if (!Number.isInteger(requirement.amount) || requirement.amount <= 0) {
                throw new RangeError("Resource amount must be positive");
            }

            combined.set(
                requirement.type,
                (combined.get(requirement.type) ?? 0) + requirement.amount
            );
        }

        for (const [type, amount] of combined) {
            const pool = this.pools.get(type);

            if (!pool) {
                throw new Error(`Unknown resource type: ${type}`);
            }

            if (!pool.canAllocate(amount)) {
                return false;
            }
        }

        for (const [type, amount] of combined) {
            this.pools.get(type).allocate(owner, amount);
        }

        return true;
    }

    release(owner) {
        let released = 0;

        for (const pool of this.pools.values()) {
            released += pool.release(owner);
        }

        return released;
    }

    snapshot() {
        return [...this.pools.values()].map(pool => ({
            name: pool.name,
            type: pool.type,
            capacity: pool.capacity,
            available: pool.available,
            allocated: pool.capacity - pool.available,
            utilizationPercent: Number((pool.utilization * 100).toFixed(2))
        }));
    }
}

class ResourceJob {
    constructor(id, owner, requirements, priority, durationMs) {
        this.id = id;
        this.owner = owner;
        this.requirements = requirements;
        this.priority = priority;
        this.durationMs = durationMs;
        this.state = JobState.QUEUED;
    }
}

class AsyncScheduler extends EventTarget {
    constructor(resourceManager) {
        super();
        this.manager = resourceManager;
        this.jobs = [];
    }

    submit(job) {
        if (job.durationMs <= 0) {
            throw new RangeError("Job duration must be positive");
        }

        this.jobs.push(job);

        this.dispatchEvent(
            new CustomEvent("jobQueued", { detail: job })
        );
    }

    async dispatch() {
        /*
         * Priority sorting is deliberately done immediately before admission.
         * A newly submitted critical job therefore gets evaluated against the
         * current capacity rather than a stale ordering.
         */
        this.jobs.sort((a, b) => b.priority - a.priority);

        for (const job of [...this.jobs]) {
            if (job.state !== JobState.QUEUED) {
                continue;
            }

            if (!this.manager.request(job.owner, job.requirements)) {
                continue;
            }

            job.state = JobState.RUNNING;
            this.dispatchEvent(
                new CustomEvent("jobStarted", { detail: job })
            );

            await this.run(job);
        }
    }

    async run(job) {
        await new Promise(resolve => setTimeout(resolve, job.durationMs));

        this.manager.release(job.owner);
        job.state = JobState.COMPLETED;

        this.dispatchEvent(
            new CustomEvent("jobCompleted", { detail: job })
        );
    }
}

function createInfrastructure() {
    const manager = new ResourceManager();

    manager.addPool("Application Workers", ResourceType.COMPUTE, 12);
    manager.addPool("Service Memory", ResourceType.MEMORY, 48);
    manager.addPool("Database Pool", ResourceType.DATABASE_CONNECTION, 24);
    manager.addPool("Object Storage", ResourceType.STORAGE, 1000);
    manager.addPool("External API Budget", ResourceType.API_QUOTA, 5000);

    return manager;
}

async function runScenario() {
    const manager = createInfrastructure();
    const scheduler = new AsyncScheduler(manager);

    scheduler.addEventListener("jobQueued", event => {
        console.log(`Queued: ${event.detail.id}`);
    });

    scheduler.addEventListener("jobStarted", event => {
        console.log(`Started: ${event.detail.id}`);
    });

    scheduler.addEventListener("jobCompleted", event => {
        console.log(`Completed: ${event.detail.id}`);
    });

    const dataPipeline = new ResourceJob(
        "daily-data-pipeline",
        "data-platform",
        [
            { type: ResourceType.COMPUTE, amount: 6 },
            { type: ResourceType.MEMORY, amount: 20 },
            { type: ResourceType.DATABASE_CONNECTION, amount: 5 }
        ],
        50,
        80
    );

    const reportJob = new ResourceJob(
        "executive-report",
        "analytics",
        [
            { type: ResourceType.COMPUTE, amount: 3 },
            { type: ResourceType.MEMORY, amount: 8 }
        ],
        20,
        40
    );

    scheduler.submit(reportJob);
    scheduler.submit(dataPipeline);

    console.log("Initial capacity:");
    console.table(manager.snapshot());

    await scheduler.dispatch();

    console.log("Final capacity:");
    console.table(manager.snapshot());
}

function demonstrateFailedAtomicRequest() {
    const manager = createInfrastructure();

    const accepted = manager.request("etl-service", [
        { type: ResourceType.COMPUTE, amount: 5 },
        { type: ResourceType.MEMORY, amount: 20 }
    ]);

    console.log("First request:", accepted);

    const rejected = manager.request("oversized-service", [
        { type: ResourceType.COMPUTE, amount: 3 },
        { type: ResourceType.MEMORY, amount: 100 }
    ]);

    console.log("Oversized request:", rejected);
    console.log("Compute remains:", manager.pools.get(ResourceType.COMPUTE).available);
}

function demonstrateQuotaValidation() {
    const manager = createInfrastructure();

    try {
        manager.request("api-client", [
            { type: ResourceType.API_QUOTA, amount: 0 }
        ]);
    } catch (error) {
        console.log("Invalid quota request rejected:", error.message);
    }
}

async function main() {
    demonstrateFailedAtomicRequest();
    demonstrateQuotaValidation();
    await runScenario();
}

main().catch(error => {
    console.error("Resource management failure:", error);
    process.exitCode = 1;
});
