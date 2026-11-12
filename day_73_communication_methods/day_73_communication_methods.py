#!/usr/bin/env python3
"""
Communication Methods: A Practical Communication Architecture Simulator.

Demonstrates:
1. Synchronous request-response communication.
2. Asynchronous message queues.
3. Publish-subscribe communication.
4. Event-driven communication.
5. Webhooks.
6. Streaming communication.
7. Broadcast communication.
8. Point-to-point communication.
9. Message validation, retries, dead-letter handling, and delivery tracking.

Python standard library only.
"""

from __future__ import annotations

import json
import logging
import time
import uuid

from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s"
)

logger = logging.getLogger("communication")


class CommunicationMethod(Enum):
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    POINT_TO_POINT = "point_to_point"
    PUBLISH_SUBSCRIBE = "publish_subscribe"
    EVENT_DRIVEN = "event_driven"
    WEBHOOK = "webhook"
    STREAMING = "streaming"
    BROADCAST = "broadcast"


class MessageStatus(Enum):
    CREATED = "created"
    QUEUED = "queued"
    DELIVERED = "delivered"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"


@dataclass
class Message:
    sender: str
    receiver: str
    content: dict[str, Any]
    method: CommunicationMethod
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str | None = None
    created_at: float = field(default_factory=time.time)
    status: MessageStatus = MessageStatus.CREATED
    attempts: int = 0

    def __post_init__(self) -> None:
        if not self.sender.strip():
            raise ValueError("Sender cannot be empty.")

        if not self.receiver.strip():
            raise ValueError("Receiver cannot be empty.")

        if not isinstance(self.content, dict):
            raise TypeError("Message content must be a dictionary.")

        if len(json.dumps(self.content, default=str)) > 65536:
            raise ValueError("Message exceeds the 64 KB size limit.")

    def serialize(self) -> str:
        return json.dumps({
            "message_id": self.message_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "method": self.method.value,
            "content": self.content,
            "status": self.status.value,
            "correlation_id": self.correlation_id
        })


class CommunicationError(Exception):
    """Base communication exception."""


class DeliveryError(CommunicationError):
    """Raised when message delivery fails."""


class CommunicationHub:
    """
    Central simulation of multiple communication mechanisms.

    This implementation is in-memory. Production systems require
    durable brokers, authentication, transport encryption and monitoring.
    """

    def __init__(self, max_retries: int = 3):
        if max_retries < 0:
            raise ValueError("Maximum retries cannot be negative.")

        self.max_retries = max_retries
        self.handlers: dict[str, Callable[[Message], Any]] = {}
        self.subscribers: dict[str, list[str]] = defaultdict(list)
        self.queues: dict[str, deque[Message]] = defaultdict(deque)
        self.dead_letters: list[Message] = []
        self.history: list[Message] = []
        self.webhook_handlers: dict[str, Callable[[Message], Any]] = {}

    def register(
        self,
        endpoint: str,
        handler: Callable[[Message], Any]
    ) -> None:
        if not endpoint.strip() or not callable(handler):
            raise ValueError("A valid endpoint and handler are required.")

        self.handlers[endpoint] = handler
        logger.info("Registered endpoint: %s", endpoint)

    def register_webhook(
        self,
        url: str,
        handler: Callable[[Message], Any]
    ) -> None:
        if not url.startswith("https://"):
            raise ValueError("Webhooks must use HTTPS.")

        self.webhook_handlers[url] = handler

    def subscribe(self, topic: str, endpoint: str) -> None:
        if endpoint not in self.handlers:
            raise ValueError("Subscriber endpoint is not registered.")

        if endpoint not in self.subscribers[topic]:
            self.subscribers[topic].append(endpoint)

    def _deliver(self, message: Message, endpoint: str) -> Any:
        handler = self.handlers.get(endpoint)

        if handler is None:
            raise DeliveryError(f"Unknown endpoint: {endpoint}")

        return handler(message)

    def synchronous(
        self,
        sender: str,
        receiver: str,
        content: dict[str, Any]
    ) -> Any:
        message = Message(
            sender,
            receiver,
            content,
            CommunicationMethod.SYNCHRONOUS
        )

        try:
            result = self._deliver(message, receiver)
            message.status = MessageStatus.DELIVERED
            return result
        except Exception as exc:
            message.status = MessageStatus.FAILED
            raise DeliveryError(str(exc)) from exc
        finally:
            self.history.append(message)

    def send_async(self, message: Message) -> None:
        message.status = MessageStatus.QUEUED
        self.queues[message.receiver].append(message)
        self.history.append(message)

    def process_queue(self, receiver: str) -> int:
        queue = self.queues[receiver]
        processed = 0

        while queue:
            message = queue.popleft()

            try:
                message.attempts += 1
                self._deliver(message, receiver)
                message.status = MessageStatus.DELIVERED
                processed += 1

            except Exception as exc:
                logger.warning(
                    "Delivery attempt %s failed: %s",
                    message.attempts,
                    exc
                )

                if message.attempts <= self.max_retries:
                    queue.append(message)
                else:
                    message.status = MessageStatus.DEAD_LETTERED
                    self.dead_letters.append(message)

        return processed

    def publish(self, topic: str, message: Message) -> int:
        """
        Publish to all current subscribers.

        Each subscriber receives an independent delivery record.
        """
        endpoints = self.subscribers.get(topic, [])

        for endpoint in endpoints:
            copy = Message(
                sender=message.sender,
                receiver=endpoint,
                content=dict(message.content),
                method=CommunicationMethod.PUBLISH_SUBSCRIBE,
                correlation_id=message.message_id
            )
            self.send_async(copy)

        return len(endpoints)

    def emit_event(self, event_type: str, payload: dict[str, Any]) -> int:
        event = Message(
            sender="event-producer",
            receiver=event_type,
            content=payload,
            method=CommunicationMethod.EVENT_DRIVEN
        )

        return self.publish(event_type, event)

    def invoke_webhook(self, url: str, message: Message) -> Any:
        handler = self.webhook_handlers.get(url)

        if handler is None:
            raise DeliveryError("Webhook endpoint not registered.")

        try:
            return handler(message)
        except Exception as exc:
            raise DeliveryError("Webhook invocation failed.") from exc

    def stream(
        self,
        sender: str,
        receiver: str,
        chunks: list[str]
    ) -> list[str]:
        """
        Simulates ordered streaming of content chunks.
        """
        if receiver not in self.handlers:
            raise DeliveryError("Streaming receiver is unavailable.")

        received = []

        for index, chunk in enumerate(chunks):
            if not isinstance(chunk, str):
                raise TypeError("Stream chunks must be strings.")

            packet = Message(
                sender,
                receiver,
                {"sequence": index, "chunk": chunk},
                CommunicationMethod.STREAMING
            )

            self._deliver(packet, receiver)
            received.append(chunk)

        return received

    def broadcast(
        self,
        sender: str,
        content: dict[str, Any]
    ) -> int:
        delivered = 0

        for endpoint in self.handlers:
            message = Message(
                sender,
                endpoint,
                dict(content),
                CommunicationMethod.BROADCAST
            )

            try:
                self._deliver(message, endpoint)
                message.status = MessageStatus.DELIVERED
                delivered += 1
            except Exception:
                message.status = MessageStatus.FAILED

            self.history.append(message)

        return delivered

    def report(self) -> dict[str, int]:
        result = defaultdict(int)

        for message in self.history:
            result[message.status.value] += 1

        result["dead_letter_count"] = len(self.dead_letters)
        return dict(result)


def main() -> None:
    hub = CommunicationHub(max_retries=2)

    received: list[dict[str, Any]] = []

    def payment_service(message: Message) -> dict[str, str]:
        received.append(message.content)
        return {"payment": "accepted"}

    def inventory_service(message: Message) -> None:
        received.append(message.content)

    def notification_service(message: Message) -> None:
        received.append(message.content)

    hub.register("payment", payment_service)
    hub.register("inventory", inventory_service)
    hub.register("notification", notification_service)

    print("\n1. Synchronous communication")

    response = hub.synchronous(
        "checkout",
        "payment",
        {"order_id": 1001, "amount": 2500}
    )
    print("Response:", response)

    print("\n2. Asynchronous communication")

    queued_message = Message(
        "checkout",
        "inventory",
        {"order_id": 1001, "action": "reserve"},
        CommunicationMethod.ASYNCHRONOUS
    )

    hub.send_async(queued_message)
    print("Processed:", hub.process_queue("inventory"))

    print("\n3. Point-to-point communication")

    point_message = Message(
        "warehouse",
        "inventory",
        {"product_id": "P101", "quantity": 5},
        CommunicationMethod.POINT_TO_POINT
    )

    hub.send_async(point_message)
    print("Processed:", hub.process_queue("inventory"))

    print("\n4. Publish-subscribe communication")

    hub.subscribe("order.created", "inventory")
    hub.subscribe("order.created", "notification")

    event = Message(
        "order-service",
        "order.created",
        {"order_id": 1002},
        CommunicationMethod.PUBLISH_SUBSCRIBE
    )

    print("Subscribers:", hub.publish("order.created", event))

    hub.process_queue("inventory")
    hub.process_queue("notification")

    print("\n5. Event-driven communication")

    hub.emit_event(
        "order.created",
        {"order_id": 1003, "priority": "high"}
    )

    hub.process_queue("inventory")
    hub.process_queue("notification")

    print("\n6. Webhook communication")

    hub.register_webhook(
        "https://example.com/hooks/orders",
        lambda msg: {"received": msg.message_id}
    )

    webhook_message = Message(
        "order-service",
        "external-system",
        {"event": "order.shipped"},
        CommunicationMethod.WEBHOOK
    )

    print(
        "Webhook response:",
        hub.invoke_webhook(
            "https://example.com/hooks/orders",
            webhook_message
        )
    )

    print("\n7. Streaming communication")

    streamed = hub.stream(
        "report-service",
        "notification",
        ["Report ", "generation ", "completed."]
    )

    print("Received:", "".join(streamed))

    print("\n8. Broadcast communication")

    print("Delivered:", hub.broadcast(
        "system-monitor",
        {"announcement": "Maintenance at 23:00"}
    ))

    print("\n9. Communication report")
    print(json.dumps(hub.report(), indent=2))

    print("\n10. Serialization")
    print(queued_message.serialize())

    assert response["payment"] == "accepted"
    assert len(streamed) == 3
    assert hub.report()["dead_letter_count"] == 0

    print("\nAll communication demonstrations completed.")


if __name__ == "__main__":
    main()
