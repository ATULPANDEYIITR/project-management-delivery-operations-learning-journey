#include <algorithm>
#include <chrono>
#include <functional>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;

enum class CommunicationMethod {
    Synchronous,
    Asynchronous,
    PointToPoint,
    PublishSubscribe,
    EventDriven,
    Webhook,
    Streaming,
    Broadcast
};

enum class MessageStatus {
    Created,
    Queued,
    Delivered,
    Failed,
    DeadLettered
};

string methodName(CommunicationMethod method) {
    switch (method) {
        case CommunicationMethod::Synchronous:
            return "Synchronous";
        case CommunicationMethod::Asynchronous:
            return "Asynchronous";
        case CommunicationMethod::PointToPoint:
            return "Point-to-point";
        case CommunicationMethod::PublishSubscribe:
            return "Publish-subscribe";
        case CommunicationMethod::EventDriven:
            return "Event-driven";
        case CommunicationMethod::Webhook:
            return "Webhook";
        case CommunicationMethod::Streaming:
            return "Streaming";
        case CommunicationMethod::Broadcast:
            return "Broadcast";
    }

    throw logic_error("Unknown communication method.");
}

string statusName(MessageStatus status) {
    switch (status) {
        case MessageStatus::Created:
            return "Created";
        case MessageStatus::Queued:
            return "Queued";
        case MessageStatus::Delivered:
            return "Delivered";
        case MessageStatus::Failed:
            return "Failed";
        case MessageStatus::DeadLettered:
            return "Dead-lettered";
    }

    throw logic_error("Unknown message status.");
}

struct Message {
    unsigned long long id;
    string sender;
    string receiver;
    string payload;
    CommunicationMethod method;
    MessageStatus status = MessageStatus::Created;
    int attempts = 0;
    unsigned long long correlationId = 0;
};

class CommunicationException : public runtime_error {
public:
    explicit CommunicationException(const string& message)
        : runtime_error(message) {}
};

class CommunicationEngine {
public:
    using Handler = function<void(const Message&)>;

private:
    unordered_map<string, Handler> services;
    unordered_map<string, queue<Message>> queues;
    unordered_map<string, set<string>> subscriptions;
    vector<Message> history;
    vector<Message> deadLetters;

    unsigned long long nextId = 1;
    int maxRetries;

    Message createMessage(
        const string& sender,
        const string& receiver,
        const string& payload,
        CommunicationMethod method,
        unsigned long long correlationId = 0
    ) {
        if (sender.empty() || receiver.empty()) {
            throw invalid_argument("Sender and receiver are required.");
        }

        if (payload.size() > 65536) {
            throw invalid_argument("Message exceeds 64 KB.");
        }

        return {
            nextId++,
            sender,
            receiver,
            payload,
            method,
            MessageStatus::Created,
            0,
            correlationId
        };
    }

    void invoke(const Message& message) {
        auto it = services.find(message.receiver);

        if (it == services.end()) {
            throw CommunicationException("Receiver unavailable.");
        }

        it->second(message);
    }

public:
    explicit CommunicationEngine(int retries = 2)
        : maxRetries(retries) {
        if (retries < 0) {
            throw invalid_argument("Retry count cannot be negative.");
        }
    }

    void registerService(const string& name, Handler handler) {
        if (name.empty() || !handler) {
            throw invalid_argument("Invalid service registration.");
        }

        if (services.count(name)) {
            throw CommunicationException("Service already registered.");
        }

        services.emplace(name, move(handler));
    }

    void synchronous(
        const string& sender,
        const string& receiver,
        const string& payload
    ) {
        Message message = createMessage(
            sender,
            receiver,
            payload,
            CommunicationMethod::Synchronous
        );

        try {
            invoke(message);
            message.status = MessageStatus::Delivered;
        } catch (...) {
            message.status = MessageStatus::Failed;
            history.push_back(message);
            throw;
        }

        history.push_back(message);
    }

    unsigned long long sendAsync(
        const string& sender,
        const string& receiver,
        const string& payload,
        CommunicationMethod method = CommunicationMethod::Asynchronous
    ) {
        Message message = createMessage(
            sender,
            receiver,
            payload,
            method
        );

        message.status = MessageStatus::Queued;
        unsigned long long id = message.id;

        queues[receiver].push(message);
        history.push_back(message);

        return id;
    }

    size_t processQueue(const string& receiver) {
        auto it = queues.find(receiver);

        if (it == queues.end()) {
            return 0;
        }

        size_t delivered = 0;

        // Retry processing is bounded to prevent an infinite retry loop.
        size_t batchSize = it->second.size();

        for (size_t i = 0; i < batchSize; ++i) {
            Message message = it->second.front();
            it->second.pop();

            try {
                ++message.attempts;
                invoke(message);
                message.status = MessageStatus::Delivered;
                ++delivered;
            } catch (const exception& error) {
                cerr << "Delivery failure: " << error.what() << '\n';

                if (message.attempts <= maxRetries) {
                    it->second.push(message);
                } else {
                    message.status = MessageStatus::DeadLettered;
                    deadLetters.push_back(message);
                }
            }
        }

        return delivered;
    }

    void subscribe(const string& topic, const string& service) {
        if (!services.count(service)) {
            throw CommunicationException("Unknown subscriber.");
        }

        subscriptions[topic].insert(service);
    }

    size_t publish(
        const string& topic,
        const string& sender,
        const string& payload
    ) {
        auto it = subscriptions.find(topic);

        if (it == subscriptions.end()) {
            return 0;
        }

        size_t count = 0;

        for (const string& subscriber : it->second) {
            Message message = createMessage(
                sender,
                subscriber,
                payload,
                CommunicationMethod::PublishSubscribe
            );

            message.status = MessageStatus::Queued;
            message.correlationId = message.id;

            queues[subscriber].push(message);
            history.push_back(message);
            ++count;
        }

        return count;
    }

    void emitEvent(
        const string& eventName,
        const string& producer,
        const string& payload
    ) {
        publish(eventName, producer, payload);
    }

    void broadcast(
        const string& sender,
        const string& payload
    ) {
        for (const auto& entry : services) {
            Message message = createMessage(
                sender,
                entry.first,
                payload,
                CommunicationMethod::Broadcast
            );

            try {
                invoke(message);
                message.status = MessageStatus::Delivered;
            } catch (const exception&) {
                message.status = MessageStatus::Failed;
            }

            history.push_back(message);
        }
    }

    void stream(
        const string& sender,
        const string& receiver,
        const vector<string>& chunks
    ) {
        if (!services.count(receiver)) {
            throw CommunicationException("Streaming receiver unavailable.");
        }

        for (size_t i = 0; i < chunks.size(); ++i) {
            ostringstream payload;
            payload << "sequence=" << i << ";data=" << chunks[i];

            Message message = createMessage(
                sender,
                receiver,
                payload.str(),
                CommunicationMethod::Streaming
            );

            invoke(message);
            message.status = MessageStatus::Delivered;
            history.push_back(message);
        }
    }

    void webhook(
        const string& sender,
        const string& receiver,
        const string& payload,
        bool secureTransport
    ) {
        if (!secureTransport) {
            throw CommunicationException(
                "Webhook requires secure HTTPS transport."
            );
        }

        Message message = createMessage(
            sender,
            receiver,
            payload,
            CommunicationMethod::Webhook
        );

        invoke(message);
        message.status = MessageStatus::Delivered;
        history.push_back(message);
    }

    void report() const {
        map<MessageStatus, size_t> counts;

        for (const auto& message : history) {
            counts[message.status]++;
        }

        cout << "\nCommunication report\n";

        for (const auto& entry : counts) {
            cout << statusName(entry.first)
                 << ": " << entry.second << '\n';
        }

        cout << "Dead letters: " << deadLetters.size() << '\n';
    }

    void printHistory() const {
        cout << "\nMessage history\n";

        for (const auto& message : history) {
            cout << "#" << message.id
                 << " | " << methodName(message.method)
                 << " | " << message.sender
                 << " -> " << message.receiver
                 << " | " << statusName(message.status)
                 << '\n';
        }
    }
};

int main() {
    try {
        CommunicationEngine engine(2);

        vector<string> received;

        auto payment = [&received](const Message& message) {
            received.push_back(message.payload);
            cout << "Payment service: " << message.payload << '\n';
        };

        auto inventory = [&received](const Message& message) {
            received.push_back(message.payload);
            cout << "Inventory service: " << message.payload << '\n';
        };

        auto notification = [&received](const Message& message) {
            received.push_back(message.payload);
            cout << "Notification service: " << message.payload << '\n';
        };

        engine.registerService("payment", payment);
        engine.registerService("inventory", inventory);
        engine.registerService("notification", notification);

        cout << "\n1. Synchronous communication\n";

        engine.synchronous(
            "checkout",
            "payment",
            "Order 1001 payment request"
        );

        cout << "\n2. Asynchronous communication\n";

        engine.sendAsync(
            "checkout",
            "inventory",
            "Reserve product P101"
        );

        engine.processQueue("inventory");

        cout << "\n3. Point-to-point communication\n";

        engine.sendAsync(
            "warehouse",
            "inventory",
            "Stock update: 50 units",
            CommunicationMethod::PointToPoint
        );

        engine.processQueue("inventory");

        cout << "\n4. Publish-subscribe communication\n";

        engine.subscribe("order.created", "inventory");
        engine.subscribe("order.created", "notification");

        cout << "Subscribers: "
             << engine.publish(
                 "order.created",
                 "order-service",
                 "Order 1002 created"
             )
             << '\n';

        engine.processQueue("inventory");
        engine.processQueue("notification");

        cout << "\n5. Event-driven communication\n";

        engine.emitEvent(
            "order.created",
            "event-producer",
            "Order 1003 created"
        );

        engine.processQueue("inventory");
        engine.processQueue("notification");

        cout << "\n6. Webhook communication\n";

        engine.webhook(
            "order-service",
            "notification",
            "Order shipped event",
            true
        );

        cout << "\n7. Streaming communication\n";

        engine.stream(
            "report-service",
            "notification",
            {"Report ", "processing ", "complete"}
        );

        cout << "\n8. Broadcast communication\n";

        engine.broadcast(
            "system-monitor",
            "Maintenance announcement"
        );

        cout << "\n9. Performance characteristics\n";
        cout << "Queue insertion: O(1) amortized\n";
        cout << "Subscriber lookup: O(log S) per lookup\n";
        cout << "Broadcast: O(N) service invocations\n";
        cout << "Queue processing: O(M) handler invocations\n";

        engine.printHistory();
        engine.report();

        if (received.size() < 5) {
            throw runtime_error("Communication validation failed.");
        }

        cout << "\nAll communication tests passed.\n";

    } catch (const exception& error) {
        cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
