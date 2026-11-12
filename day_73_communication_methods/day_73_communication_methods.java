import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;

/**
 * Enterprise Communication Management System.
 *
 * Java 17, standard library only.
 *
 * Communication patterns:
 * - Request-response
 * - Asynchronous messaging
 * - Point-to-point
 * - Publish-subscribe
 * - Event-driven
 * - Webhooks
 * - Streaming
 * - Broadcast
 *
 * Includes delivery tracking, retries, subscriber management,
 * immutable messages and asynchronous execution.
 */
public class CommunicationMethods {

    enum Method {
        REQUEST_RESPONSE,
        ASYNCHRONOUS,
        POINT_TO_POINT,
        PUBLISH_SUBSCRIBE,
        EVENT_DRIVEN,
        WEBHOOK,
        STREAMING,
        BROADCAST
    }

    enum Status {
        CREATED,
        QUEUED,
        PROCESSING,
        DELIVERED,
        FAILED,
        DEAD_LETTERED
    }

    record Message(
        UUID id,
        String sender,
        String receiver,
        Map<String, String> payload,
        Method method,
        UUID correlationId,
        Instant createdAt
    ) {
        Message {
            Objects.requireNonNull(id);
            Objects.requireNonNull(method);
            Objects.requireNonNull(createdAt);

            if (sender == null || sender.isBlank()) {
                throw new IllegalArgumentException("Sender is required.");
            }

            if (receiver == null || receiver.isBlank()) {
                throw new IllegalArgumentException("Receiver is required.");
            }

            Objects.requireNonNull(payload, "Payload is required.");

            if (payload.size() > 100) {
                throw new IllegalArgumentException("Too many payload fields.");
            }

            int totalLength = payload.entrySet()
                .stream()
                .mapToInt(entry ->
                    entry.getKey().length() + entry.getValue().length()
                )
                .sum();

            if (totalLength > 65536) {
                throw new IllegalArgumentException("Payload too large.");
            }

            payload = Collections.unmodifiableMap(
                new HashMap<>(payload)
            );
        }

        static Message create(
            String sender,
            String receiver,
            Map<String, String> payload,
            Method method
        ) {
            return new Message(
                UUID.randomUUID(),
                sender,
                receiver,
                payload,
                method,
                null,
                Instant.now()
            );
        }
    }

    record DeliveryRecord(
        UUID messageId,
        String receiver,
        Status status,
        int attempts,
        String detail,
        Instant timestamp
    ) {}

    @FunctionalInterface
    interface MessageHandler {
        void handle(Message message) throws Exception;
    }

    static class CommunicationException extends RuntimeException {
        CommunicationException(String message) {
            super(message);
        }

        CommunicationException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    static class RetryPolicy {
        private final int maxAttempts;

        RetryPolicy(int maxAttempts) {
            if (maxAttempts < 1) {
                throw new IllegalArgumentException(
                    "At least one attempt is required."
                );
            }

            this.maxAttempts = maxAttempts;
        }

        boolean shouldRetry(int attempts) {
            return attempts < maxAttempts;
        }

        int maxAttempts() {
            return maxAttempts;
        }
    }

    static class ReviewPolicy {
        private final int requiredSubscribers;

        ReviewPolicy(int requiredSubscribers) {
            if (requiredSubscribers < 0) {
                throw new IllegalArgumentException(
                    "Subscriber requirement cannot be negative."
                );
            }

            this.requiredSubscribers = requiredSubscribers;
        }

        boolean satisfied(int actualSubscribers) {
            return actualSubscribers >= requiredSubscribers;
        }
    }

    static class CommunicationService implements AutoCloseable {

        private final Map<String, MessageHandler> handlers =
            new ConcurrentHashMap<>();

        private final Map<String, ArrayDeque<Message>> queues =
            new ConcurrentHashMap<>();

        private final Map<String, Set<String>> topics =
            new ConcurrentHashMap<>();

        private final List<DeliveryRecord> deliveryHistory =
            Collections.synchronizedList(new ArrayList<>());

        private final List<DeliveryRecord> deadLetters =
            Collections.synchronizedList(new ArrayList<>());

        private final ExecutorService executor =
            Executors.newFixedThreadPool(4);

        private final RetryPolicy retryPolicy;

        private final AtomicInteger activeDeliveries =
            new AtomicInteger();

        CommunicationService(RetryPolicy retryPolicy) {
            this.retryPolicy = retryPolicy;
        }

        void register(String name, MessageHandler handler) {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Invalid service name.");
            }

            Objects.requireNonNull(handler);

            if (handlers.putIfAbsent(name, handler) != null) {
                throw new CommunicationException(
                    "Service already registered: " + name
                );
            }

            queues.put(name, new ArrayDeque<>());
        }

        private MessageHandler getHandler(String name) {
            MessageHandler handler = handlers.get(name);

            if (handler == null) {
                throw new CommunicationException(
                    "Service unavailable: " + name
                );
            }

            return handler;
        }

        CompletableFuture<Void> requestResponse(
            String sender,
            String receiver,
            Map<String, String> payload
        ) {
            Message message = Message.create(
                sender,
                receiver,
                payload,
                Method.REQUEST_RESPONSE
            );

            return CompletableFuture.runAsync(() -> {
                try {
                    getHandler(receiver).handle(message);

                    record(
                        message,
                        Status.DELIVERED,
                        1,
                        "Synchronous request completed."
                    );
                } catch (Exception exception) {
                    record(
                        message,
                        Status.FAILED,
                        1,
                        exception.getMessage()
                    );

                    throw new CompletionException(exception);
                }
            }, executor);
        }

        void send(
            String sender,
            String receiver,
            Map<String, String> payload
        ) {
            Message message = Message.create(
                sender,
                receiver,
                payload,
                Method.ASYNCHRONOUS
            );

            enqueue(message);
        }

        private void enqueue(Message message) {
            ArrayDeque<Message> queue = queues.get(message.receiver());

            if (queue == null) {
                throw new CommunicationException("Queue unavailable.");
            }

            synchronized (queue) {
                queue.addLast(message);
            }

            record(message, Status.QUEUED, 0, "Message queued.");
        }

        CompletableFuture<Integer> processQueue(String receiver) {
            ArrayDeque<Message> queue = queues.get(receiver);

            if (queue == null) {
                throw new CommunicationException("Unknown queue.");
            }

            return CompletableFuture.supplyAsync(() -> {
                int delivered = 0;

                while (true) {
                    Message message;

                    synchronized (queue) {
                        message = queue.pollFirst();
                    }

                    if (message == null) {
                        break;
                    }

                    if (deliverWithRetry(message)) {
                        delivered++;
                    }
                }

                return delivered;
            }, executor);
        }

        private boolean deliverWithRetry(Message message) {
            MessageHandler handler = getHandler(message.receiver());

            for (int attempt = 1;
                 attempt <= retryPolicy.maxAttempts();
                 attempt++) {

                activeDeliveries.incrementAndGet();

                try {
                    handler.handle(message);

                    record(
                        message,
                        Status.DELIVERED,
                        attempt,
                        "Delivery completed."
                    );

                    return true;

                } catch (Exception exception) {
                    boolean retry = retryPolicy.shouldRetry(attempt);

                    if (!retry) {
                        DeliveryRecord record = new DeliveryRecord(
                            message.id(),
                            message.receiver(),
                            Status.DEAD_LETTERED,
                            attempt,
                            exception.getMessage(),
                            Instant.now()
                        );

                        deadLetters.add(record);
                        deliveryHistory.add(record);
                        return false;
                    }

                } finally {
                    activeDeliveries.decrementAndGet();
                }
            }

            return false;
        }

        void subscribe(String topic, String service) {
            getHandler(service);

            topics.computeIfAbsent(
                topic,
                ignored -> ConcurrentHashMap.newKeySet()
            ).add(service);
        }

        int publish(
            String topic,
            String sender,
            Map<String, String> payload
        ) {
            Set<String> subscribers = topics.getOrDefault(
                topic,
                Collections.emptySet()
            );

            int count = 0;

            for (String subscriber : subscribers) {
                Message message = Message.create(
                    sender,
                    subscriber,
                    payload,
                    Method.PUBLISH_SUBSCRIBE
                );

                enqueue(message);
                count++;
            }

            return count;
        }

        void emitEvent(String eventName, Map<String, String> payload) {
            publish(eventName, "event-producer", payload);
        }

        void webhook(
            String endpoint,
            boolean secureTransport,
            String sender,
            Map<String, String> payload
        ) {
            if (!secureTransport || !endpoint.startsWith("https://")) {
                throw new CommunicationException(
                    "Webhook requires HTTPS."
                );
            }

            Message message = Message.create(
                sender,
                endpoint,
                payload,
                Method.WEBHOOK
            );

            // Webhook receivers must be registered as services.
            try {
                getHandler(endpoint).handle(message);

                record(
                    message,
                    Status.DELIVERED,
                    1,
                    "Webhook accepted."
                );
            } catch (Exception exception) {
                record(
                    message,
                    Status.FAILED,
                    1,
                    exception.getMessage()
                );

                throw new CommunicationException(
                    "Webhook delivery failed.",
                    exception
                );
            }
        }

        void stream(
            String sender,
            String receiver,
            List<String> chunks
        ) {
            MessageHandler handler = getHandler(receiver);

            for (int i = 0; i < chunks.size(); i++) {
                Map<String, String> payload = Map.of(
                    "sequence", Integer.toString(i),
                    "chunk", Objects.requireNonNull(chunks.get(i))
                );

                Message message = Message.create(
                    sender,
                    receiver,
                    payload,
                    Method.STREAMING
                );

                try {
                    handler.handle(message);

                    record(
                        message,
                        Status.DELIVERED,
                        1,
                        "Stream chunk delivered."
                    );
                } catch (Exception exception) {
                    record(
                        message,
                        Status.FAILED,
                        1,
                        exception.getMessage()
                    );

                    throw new CommunicationException(
                        "Streaming interrupted.",
                        exception
                    );
                }
            }
        }

        void broadcast(
            String sender,
            Map<String, String> payload
        ) {
            for (String receiver : handlers.keySet()) {
                Message message = Message.create(
                    sender,
                    receiver,
                    payload,
                    Method.BROADCAST
                );

                try {
                    getHandler(receiver).handle(message);

                    record(
                        message,
                        Status.DELIVERED,
                        1,
                        "Broadcast delivered."
                    );
                } catch (Exception exception) {
                    record(
                        message,
                        Status.FAILED,
                        1,
                        exception.getMessage()
                    );
                }
            }
        }

        private void record(
            Message message,
            Status status,
            int attempts,
            String detail
        ) {
            deliveryHistory.add(new DeliveryRecord(
                message.id(),
                message.receiver(),
                status,
                attempts,
                detail == null ? "No detail" : detail,
                Instant.now()
            ));
        }

        Map<Status, Long> report() {
            EnumMap<Status, Long> result = new EnumMap<>(Status.class);

            for (Status status : Status.values()) {
                result.put(status, 0L);
            }

            synchronized (deliveryHistory) {
                for (DeliveryRecord record : deliveryHistory) {
                    result.merge(record.status(), 1L, Long::sum);
                }
            }

            return result;
        }

        int activeDeliveries() {
            return activeDeliveries.get();
        }

        List<DeliveryRecord> getDeadLetters() {
            synchronized (deadLetters) {
                return List.copyOf(deadLetters);
            }
        }

        private void shutdown() {
            executor.shutdown();

            try {
                if (!executor.awaitTermination(5, TimeUnit.SECONDS)) {
                    executor.shutdownNow();
                }
            } catch (InterruptedException exception) {
                executor.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }

        @Override
        public void close() {
            shutdown();
        }
    }

    public static void main(String[] args) {
        try (CommunicationService service =
                 new CommunicationService(new RetryPolicy(3))) {

            List<String> received =
                Collections.synchronizedList(new ArrayList<>());

            service.register("payment", message ->
                received.add("Payment: " + message.payload())
            );

            service.register("inventory", message ->
                received.add("Inventory: " + message.payload())
            );

            service.register("notifications", message ->
                received.add("Notification: " + message.payload())
            );

            service.register("https://example.com/hooks/orders", message ->
                received.add("Webhook: " + message.payload())
            );

            System.out.println("\n1. Request-response");

            service.requestResponse(
                "checkout",
                "payment",
                Map.of("orderId", "1001", "amount", "2500")
            ).join();

            System.out.println("\n2. Asynchronous messaging");

            service.send(
                "checkout",
                "inventory",
                Map.of("operation", "reserve", "orderId", "1001")
            );

            service.processQueue("inventory").join();

            System.out.println("\n3. Point-to-point");

            service.send(
                "warehouse",
                "inventory",
                Map.of("operation", "stock_update", "quantity", "50")
            );

            service.processQueue("inventory").join();

            System.out.println("\n4. Publish-subscribe");

            service.subscribe("order.created", "inventory");
            service.subscribe("order.created", "notifications");

            int subscribers = service.publish(
                "order.created",
                "order-service",
                Map.of("orderId", "1002")
            );

            System.out.println("Subscribers: " + subscribers);

            service.processQueue("inventory").join();
            service.processQueue("notifications").join();

            System.out.println("\n5. Event-driven");

            service.emitEvent(
                "order.created",
                Map.of("orderId", "1003")
            );

            service.processQueue("inventory").join();
            service.processQueue("notifications").join();

            System.out.println("\n6. Webhook");

            service.webhook(
                "https://example.com/hooks/orders",
                true,
                "order-service",
                Map.of("event", "order.shipped")
            );

            System.out.println("\n7. Streaming");

            service.stream(
                "report-service",
                "notifications",
                List.of("Report ", "processing ", "completed.")
            );

            System.out.println("\n8. Broadcast");

            service.broadcast(
                "system-monitor",
                Map.of("announcement", "Maintenance scheduled")
            );

            System.out.println("\n9. Enterprise delivery report");

            service.report().forEach((status, count) ->
                System.out.println(status + ": " + count)
            );

            System.out.println(
                "Dead letters: " + service.getDeadLetters().size()
            );

            if (received.size() < 5) {
                throw new IllegalStateException(
                    "Communication validation failed."
                );
            }

            System.out.println("\nEnterprise communication tests passed.");
        }
    }
}
