"use strict";

/*
 * Communication Methods: Event-driven communication architecture.
 *
 * Implements:
 * - Request-response
 * - Asynchronous messaging
 * - Point-to-point queues
 * - Publish-subscribe
 * - Event-driven processing
 * - Webhooks
 * - Streaming
 * - Broadcast
 * - Retry policies
 * - Dead-letter handling
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const { EventEmitter } = require("node:events");
const { randomUUID } = require("node:crypto");
const { setTimeout: delay } = require("node:timers/promises");

const Method = Object.freeze({
    REQUEST_RESPONSE: "request_response",
    ASYNCHRONOUS: "asynchronous",
    POINT_TO_POINT: "point_to_point",
    PUBLISH_SUBSCRIBE: "publish_subscribe",
    EVENT_DRIVEN: "event_driven",
    WEBHOOK: "webhook",
    STREAMING: "streaming",
    BROADCAST: "broadcast"
});

const Status = Object.freeze({
    CREATED: "created",
    QUEUED: "queued",
    PROCESSING: "processing",
    DELIVERED: "delivered",
    FAILED: "failed",
    DEAD_LETTERED: "dead_lettered"
});

class CommunicationError extends Error {
    constructor(message, code = "COMMUNICATION_ERROR") {
        super(message);
        this.name = "CommunicationError";
        this.code = code;
    }
}

class Message {
    constructor({ sender, receiver, payload, method, correlationId = null }) {
        if (typeof sender !== "string" || !sender.trim()) {
            throw new TypeError("Sender must be a non-empty string.");
        }

        if (typeof receiver !== "string" || !receiver.trim()) {
            throw new TypeError("Receiver must be a non-empty string.");
        }

        if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
            throw new TypeError("Payload must be an object.");
        }

        if (!Object.values(Method).includes(method)) {
            throw new TypeError("Unsupported communication method.");
        }

        const serialized = JSON.stringify(payload);

        if (Buffer.byteLength(serialized, "utf8") > 65536) {
            throw new RangeError("Payload exceeds 64 KB.");
        }

        this.id = randomUUID();
        this.sender = sender;
        this.receiver = receiver;
        this.payload = structuredClone(payload);
        this.method = method;
        this.correlationId = correlationId;
        this.createdAt = new Date().toISOString();
        this.status = Status.CREATED;
        this.attempts = 0;
    }
}

class MessageQueue {
    constructor() {
        this.pending = [];
        this.deadLetters = [];
        this.processing = false;
    }

    enqueue(message) {
        message.status = Status.QUEUED;
        this.pending.push(message);
    }

    get size() {
        return this.pending.length;
    }

    async process(handler, maxRetries = 3) {
        if (this.processing) {
            throw new CommunicationError(
                "Queue processing is already active.",
                "QUEUE_BUSY"
            );
        }

        this.processing = true;
        let delivered = 0;

        try {
            while (this.pending.length > 0) {
                const message = this.pending.shift();
                message.status = Status.PROCESSING;

                try {
                    message.attempts++;
                    await handler(message);
                    message.status = Status.DELIVERED;
                    delivered++;
                } catch (error) {
                    if (message.attempts <= maxRetries) {
                        message.status = Status.QUEUED;
                        this.pending.push(message);
                    } else {
                        message.status = Status.DEAD_LETTERED;
                        this.deadLetters.push({
                            message,
                            error: error.message,
                            failedAt: new Date().toISOString()
                        });
                    }
                }
            }
        } finally {
            this.processing = false;
        }

        return delivered;
    }
}

class CommunicationPlatform {
    constructor({ maxRetries = 3 } = {}) {
        if (!Number.isInteger(maxRetries) || maxRetries < 0) {
            throw new RangeError("Invalid retry configuration.");
        }

        this.maxRetries = maxRetries;
        this.services = new Map();
        this.queues = new Map();
        this.topics = new Map();
        this.webhooks = new Map();
        this.events = new EventEmitter();
        this.events.setMaxListeners(100);
        this.history = [];
        this.activeRequests = new Set();
    }

    registerService(name, handler) {
        if (!name.trim() || typeof handler !== "function") {
            throw new TypeError("Valid service name and handler required.");
        }

        this.services.set(name, handler);
        this.queues.set(name, new MessageQueue());
    }

    createMessage(sender, receiver, payload, method) {
        return new Message({ sender, receiver, payload, method });
    }

    async requestResponse(sender, receiver, payload, timeoutMs = 3000) {
        const handler = this.services.get(receiver);

        if (!handler) {
            throw new CommunicationError("Service not found.");
        }

        const message = this.createMessage(
            sender,
            receiver,
            payload,
            Method.REQUEST_RESPONSE
        );

        const requestId = message.id;
        this.activeRequests.add(requestId);

        try {
            const timeout = new Promise((_, reject) => {
                const timer = setTimeout(() => {
                    reject(new CommunicationError("Request timed out."));
                }, timeoutMs);

                timer.unref?.();
            });

            return await Promise.race([
                Promise.resolve().then(() => handler(message)),
                timeout
            ]);
        } finally {
            this.activeRequests.delete(requestId);
            this.history.push(message);
        }
    }

    send(sender, receiver, payload) {
        const queue = this.queues.get(receiver);

        if (!queue) {
            throw new CommunicationError("Unknown receiver.");
        }

        const message = this.createMessage(
            sender,
            receiver,
            payload,
            Method.ASYNCHRONOUS
        );

        queue.enqueue(message);
        this.history.push(message);

        return message.id;
    }

    async processQueue(receiver) {
        const queue = this.queues.get(receiver);
        const handler = this.services.get(receiver);

        if (!queue || !handler) {
            throw new CommunicationError("Queue or service not found.");
        }

        return queue.process(handler, this.maxRetries);
    }

    subscribe(topic, serviceName) {
        if (!this.services.has(serviceName)) {
            throw new CommunicationError("Subscriber does not exist.");
        }

        if (!this.topics.has(topic)) {
            this.topics.set(topic, new Set());
        }

        this.topics.get(topic).add(serviceName);
    }

    async publish(topic, sender, payload) {
        const subscribers = this.topics.get(topic) || new Set();
        const deliveries = [];

        for (const serviceName of subscribers) {
            const message = this.createMessage(
                sender,
                serviceName,
                payload,
                Method.PUBLISH_SUBSCRIBE
            );

            this.queues.get(serviceName).enqueue(message);
            this.history.push(message);

            deliveries.push(message.id);
        }

        return deliveries;
    }

    onEvent(eventName, handler) {
        if (typeof handler !== "function") {
            throw new TypeError("Event handler must be a function.");
        }

        this.events.on(eventName, handler);
    }

    emitEvent(eventName, payload) {
        this.events.emit(eventName, structuredClone(payload));
    }

    registerWebhook(endpoint, secret, handler) {
        if (!endpoint.startsWith("https://")) {
            throw new CommunicationError("HTTPS is required.");
        }

        if (!secret || secret.length < 32) {
            throw new CommunicationError(
                "Webhook signing secret must contain at least 32 characters."
            );
        }

        if (typeof handler !== "function") {
            throw new TypeError("Webhook handler must be a function.");
        }

        this.webhooks.set(endpoint, { secret, handler });
    }

    async invokeWebhook(endpoint, payload) {
        const webhook = this.webhooks.get(endpoint);

        if (!webhook) {
            throw new CommunicationError("Webhook not registered.");
        }

        const message = this.createMessage(
            "external-service",
            endpoint,
            payload,
            Method.WEBHOOK
        );

        const result = await webhook.handler(message);
        message.status = Status.DELIVERED;
        this.history.push(message);

        return result;
    }

    async *stream(sender, receiver, chunks) {
        if (!this.services.has(receiver)) {
            throw new CommunicationError("Streaming receiver not found.");
        }

        for (let index = 0; index < chunks.length; index++) {
            const message = this.createMessage(
                sender,
                receiver,
                { sequence: index, chunk: chunks[index] },
                Method.STREAMING
            );

            await this.services.get(receiver)(message);
            this.history.push(message);

            yield {
                sequence: index,
                data: chunks[index]
            };
        }
    }

    async broadcast(sender, payload) {
        const results = [];

        for (const [name, handler] of this.services) {
            const message = this.createMessage(
                sender,
                name,
                payload,
                Method.BROADCAST
            );

            try {
                await handler(message);
                message.status = Status.DELIVERED;
            } catch (error) {
                message.status = Status.FAILED;
            }

            this.history.push(message);
            results.push(message);
        }

        return results;
    }

    getReport() {
        const report = Object.fromEntries(
            Object.values(Status).map(status => [status, 0])
        );

        for (const message of this.history) {
            report[message.status]++;
        }

        for (const queue of this.queues.values()) {
            report.dead_lettered += queue.deadLetters.length;
        }

        return report;
    }
}

async function main() {
    const platform = new CommunicationPlatform({ maxRetries: 2 });
    const received = [];

    platform.registerService("payment", async message => {
        received.push(message.payload);
        return { paymentStatus: "approved" };
    });

    platform.registerService("inventory", async message => {
        received.push(message.payload);
        return { inventoryStatus: "reserved" };
    });

    platform.registerService("notifications", async message => {
        received.push(message.payload);
        return { notificationStatus: "sent" };
    });

    console.log("\n1. Request-response");

    const response = await platform.requestResponse(
        "checkout",
        "payment",
        { orderId: 1001, amount: 2500 }
    );

    console.log(response);

    console.log("\n2. Asynchronous messaging");

    platform.send("checkout", "inventory", {
        orderId: 1001,
        operation: "reserve"
    });

    await platform.processQueue("inventory");

    console.log("\n3. Point-to-point communication");

    platform.send("warehouse", "inventory", {
        productId: "P101",
        quantity: 10
    });

    await platform.processQueue("inventory");

    console.log("\n4. Publish-subscribe");

    platform.subscribe("order.created", "inventory");
    platform.subscribe("order.created", "notifications");

    await platform.publish("order.created", "order-service", {
        orderId: 1002
    });

    await platform.processQueue("inventory");
    await platform.processQueue("notifications");

    console.log("\n5. Event-driven communication");

    platform.onEvent("payment.completed", async payload => {
        received.push(payload);
    });

    platform.emitEvent("payment.completed", {
        transactionId: "TX9001"
    });

    await delay(10);

    console.log("\n6. Webhooks");

    platform.registerWebhook(
        "https://example.com/hooks/orders",
        "a-long-random-secret-for-webhook-signing-123456",
        async message => ({
            accepted: true,
            id: message.id
        })
    );

    console.log(
        await platform.invokeWebhook(
            "https://example.com/hooks/orders",
            { event: "order.shipped" }
        )
    );

    console.log("\n7. Streaming");

    let streamed = "";

    for await (const packet of platform.stream(
        "report-service",
        "notifications",
        ["Communication ", "completed ", "successfully."]
    )) {
        streamed += packet.data;
    }

    console.log(streamed);

    console.log("\n8. Broadcast");

    const broadcastResults = await platform.broadcast(
        "system-monitor",
        { announcement: "Scheduled maintenance" }
    );

    console.log("Recipients:", broadcastResults.length);

    console.log("\n9. Delivery report");

    console.log(JSON.stringify(platform.getReport(), null, 2));

    if (response.paymentStatus !== "approved") {
        throw new Error("Payment assertion failed.");
    }

    if (received.length < 5) {
        throw new Error("Communication test assertion failed.");
    }

    console.log("\nCommunication architecture simulation completed.");
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
