-- ============================================================
-- COMMUNICATION METHODS MANAGEMENT SYSTEM
-- PostgreSQL 15+
--
-- Models:
-- 1. Synchronous request-response
-- 2. Asynchronous messaging
-- 3. Point-to-point delivery
-- 4. Publish-subscribe
-- 5. Event-driven communication
-- 6. Webhooks
-- 7. Streaming
-- 8. Broadcast
--
-- Includes:
-- Message lifecycle, subscriptions, delivery attempts,
-- retries, dead letters, service registration and reporting.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS communication;

SET search_path TO communication, public;

-- ============================================================
-- ENUM TYPES
-- ============================================================

CREATE TYPE communication_method AS ENUM (
    'synchronous',
    'asynchronous',
    'point_to_point',
    'publish_subscribe',
    'event_driven',
    'webhook',
    'streaming',
    'broadcast'
);

CREATE TYPE message_status AS ENUM (
    'created',
    'queued',
    'processing',
    'delivered',
    'failed',
    'dead_lettered'
);

CREATE TYPE service_status AS ENUM (
    'active',
    'inactive',
    'maintenance'
);

CREATE TYPE delivery_status AS ENUM (
    'pending',
    'delivered',
    'failed',
    'dead_lettered'
);

-- ============================================================
-- SERVICES
-- ============================================================

CREATE TABLE communication_services (
    service_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    service_name VARCHAR(100) NOT NULL UNIQUE,

    service_description TEXT,

    endpoint TEXT,

    transport_protocol VARCHAR(20) NOT NULL
        DEFAULT 'internal'
        CHECK (
            transport_protocol IN (
                'internal',
                'https',
                'amqp',
                'mqtt',
                'grpc',
                'websocket',
                'tcp'
            )
        ),

    status service_status NOT NULL DEFAULT 'active',

    registered_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_endpoint CHECK (
        endpoint IS NULL OR
        endpoint ~ '^https://'
    )
);

-- ============================================================
-- COMMUNICATION CHANNELS
-- ============================================================

CREATE TABLE communication_channels (
    channel_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    channel_name VARCHAR(100) NOT NULL UNIQUE,

    method communication_method NOT NULL,

    description TEXT,

    durable BOOLEAN NOT NULL DEFAULT FALSE,

    max_retries INTEGER NOT NULL DEFAULT 3
        CHECK (max_retries BETWEEN 0 AND 20),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TOPICS
-- ============================================================

CREATE TABLE communication_topics (
    topic_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    topic_name VARCHAR(150) NOT NULL UNIQUE,

    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SUBSCRIPTIONS
-- ============================================================

CREATE TABLE communication_subscriptions (
    subscription_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    topic_id BIGINT NOT NULL
        REFERENCES communication_topics(topic_id),

    service_id BIGINT NOT NULL
        REFERENCES communication_services(service_id),

    active BOOLEAN NOT NULL DEFAULT TRUE,

    subscribed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (topic_id, service_id)
);

-- ============================================================
-- MESSAGES
-- ============================================================

CREATE TABLE communication_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    sender_service_id BIGINT NOT NULL
        REFERENCES communication_services(service_id),

    receiver_service_id BIGINT
        REFERENCES communication_services(service_id),

    channel_id BIGINT NOT NULL
        REFERENCES communication_channels(channel_id),

    topic_id BIGINT
        REFERENCES communication_topics(topic_id),

    method communication_method NOT NULL,

    correlation_id UUID,

    idempotency_key VARCHAR(150),

    payload JSONB NOT NULL,

    status message_status NOT NULL DEFAULT 'created',

    priority SMALLINT NOT NULL DEFAULT 5
        CHECK (priority BETWEEN 1 AND 10),

    attempt_count INTEGER NOT NULL DEFAULT 0
        CHECK (attempt_count >= 0),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    scheduled_at TIMESTAMPTZ,

    delivered_at TIMESTAMPTZ,

    CONSTRAINT payload_is_object CHECK (
        jsonb_typeof(payload) = 'object'
    ),

    CONSTRAINT payload_size_limit CHECK (
        octet_length(payload::text) <= 65536
    ),

    CONSTRAINT valid_message_routing CHECK (
        (
            method = 'publish_subscribe'
            AND topic_id IS NOT NULL
        )
        OR
        (
            method <> 'publish_subscribe'
            AND receiver_service_id IS NOT NULL
        )
        OR
        (
            method = 'event_driven'
            AND topic_id IS NOT NULL
        )
    )
);

CREATE UNIQUE INDEX uq_message_idempotency
ON communication_messages(sender_service_id, idempotency_key)
WHERE idempotency_key IS NOT NULL;

CREATE INDEX idx_message_status_created
ON communication_messages(status, created_at);

CREATE INDEX idx_message_receiver_status
ON communication_messages(receiver_service_id, status);

CREATE INDEX idx_message_topic
ON communication_messages(topic_id, created_at);

CREATE INDEX idx_message_correlation
ON communication_messages(correlation_id)
WHERE correlation_id IS NOT NULL;

CREATE INDEX idx_message_payload_gin
ON communication_messages USING GIN(payload);

-- ============================================================
-- DELIVERY RECORDS
-- ============================================================

CREATE TABLE communication_deliveries (
    delivery_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    message_id UUID NOT NULL
        REFERENCES communication_messages(message_id),

    receiver_service_id BIGINT NOT NULL
        REFERENCES communication_services(service_id),

    status delivery_status NOT NULL DEFAULT 'pending',

    attempt_number INTEGER NOT NULL DEFAULT 0
        CHECK (attempt_number >= 0),

    error_message TEXT,

    delivered_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(message_id, receiver_service_id)
);

CREATE INDEX idx_delivery_status
ON communication_deliveries(status, created_at);

CREATE INDEX idx_delivery_receiver
ON communication_deliveries(receiver_service_id, status);

-- ============================================================
-- DELIVERY ATTEMPTS
-- ============================================================

CREATE TABLE communication_delivery_attempts (
    attempt_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    delivery_id BIGINT NOT NULL
        REFERENCES communication_deliveries(delivery_id),

    attempt_number INTEGER NOT NULL CHECK (attempt_number > 0),

    successful BOOLEAN NOT NULL,

    error_message TEXT,

    attempted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(delivery_id, attempt_number)
);

-- ============================================================
-- DEAD LETTER QUEUE
-- ============================================================

CREATE TABLE communication_dead_letters (
    dead_letter_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    delivery_id BIGINT NOT NULL UNIQUE
        REFERENCES communication_deliveries(delivery_id),

    failure_reason TEXT NOT NULL,

    original_payload JSONB NOT NULL,

    dead_lettered_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    replayed_at TIMESTAMPTZ
);

-- ============================================================
-- STREAMING CHUNKS
-- ============================================================

CREATE TABLE communication_stream_chunks (
    chunk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    message_id UUID NOT NULL
        REFERENCES communication_messages(message_id),

    sequence_number INTEGER NOT NULL CHECK (sequence_number >= 0),

    chunk_payload TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(message_id, sequence_number)
);

-- ============================================================
-- WEBHOOK CONFIGURATION
-- ============================================================

CREATE TABLE communication_webhooks (
    webhook_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    service_id BIGINT NOT NULL
        REFERENCES communication_services(service_id),

    endpoint TEXT NOT NULL,

    secret_reference TEXT NOT NULL,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    timeout_ms INTEGER NOT NULL DEFAULT 5000
        CHECK (timeout_ms BETWEEN 100 AND 60000),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT webhook_https_only CHECK (
        endpoint ~ '^https://'
    ),

    UNIQUE(service_id, endpoint)
);

-- ============================================================
-- COMMUNICATION POLICIES
-- ============================================================

CREATE TABLE communication_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_name VARCHAR(150) NOT NULL UNIQUE,

    communication_method communication_method NOT NULL,

    max_retries INTEGER NOT NULL DEFAULT 3
        CHECK (max_retries BETWEEN 0 AND 20),

    require_durable_delivery BOOLEAN NOT NULL DEFAULT FALSE,

    require_secure_transport BOOLEAN NOT NULL DEFAULT TRUE,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- MESSAGE STATUS AUDIT
-- ============================================================

CREATE TABLE communication_status_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    message_id UUID NOT NULL
        REFERENCES communication_messages(message_id),

    previous_status message_status,

    new_status message_status NOT NULL,

    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- STATUS CHANGE TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION log_message_status_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO communication_status_audit (
            message_id,
            previous_status,
            new_status
        )
        VALUES (
            NEW.message_id,
            OLD.status,
            NEW.status
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_message_status_audit
AFTER UPDATE OF status
ON communication_messages
FOR EACH ROW
EXECUTE FUNCTION log_message_status_change();

-- ============================================================
-- SERVICE REGISTRATION AND SAMPLE DATA
-- ============================================================

INSERT INTO communication_services (
    service_name,
    service_description,
    endpoint,
    transport_protocol
)
VALUES
(
    'checkout',
    'Customer checkout service',
    NULL,
    'internal'
),
(
    'payment',
    'Payment processing service',
    NULL,
    'internal'
),
(
    'inventory',
    'Inventory management service',
    NULL,
    'internal'
),
(
    'notifications',
    'Customer notification service',
    NULL,
    'internal'
),
(
    'external_orders',
    'External order integration',
    'https://example.com/hooks/orders',
    'https'
);

INSERT INTO communication_channels (
    channel_name,
    method,
    description,
    durable,
    max_retries
)
VALUES
(
    'request_response_channel',
    'synchronous',
    'Immediate request-response interaction',
    FALSE,
    0
),
(
    'async_message_queue',
    'asynchronous',
    'Durable background message processing',
    TRUE,
    3
),
(
    'inventory_direct_channel',
    'point_to_point',
    'Direct inventory service communication',
    TRUE,
    3
),
(
    'order_event_channel',
    'publish_subscribe',
    'Order event distribution',
    TRUE,
    5
),
(
    'business_event_channel',
    'event_driven',
    'Event-driven service integration',
    TRUE,
    5
),
(
    'webhook_channel',
    'webhook',
    'External HTTPS integrations',
    TRUE,
    3
),
(
    'stream_channel',
    'streaming',
    'Sequential stream processing',
    TRUE,
    2
),
(
    'broadcast_channel',
    'broadcast',
    'System-wide announcements',
    FALSE,
    1
);

INSERT INTO communication_topics(topic_name, description)
VALUES
(
    'order.created',
    'New order creation events'
),
(
    'payment.completed',
    'Successful payment events'
),
(
    'inventory.updated',
    'Inventory state changes'
);

INSERT INTO communication_subscriptions(
    topic_id,
    service_id
)
SELECT
    t.topic_id,
    s.service_id
FROM communication_topics t
CROSS JOIN communication_services s
WHERE
    (
        t.topic_name = 'order.created'
        AND s.service_name IN ('inventory', 'notifications')
    )
    OR
    (
        t.topic_name = 'payment.completed'
        AND s.service_name = 'notifications'
    );

INSERT INTO communication_policies (
    policy_name,
    communication_method,
    max_retries,
    require_durable_delivery,
    require_secure_transport
)
VALUES
(
    'Synchronous API Policy',
    'synchronous',
    0,
    FALSE,
    TRUE
),
(
    'Durable Queue Policy',
    'asynchronous',
    3,
    TRUE,
    TRUE
),
(
    'External Webhook Policy',
    'webhook',
    3,
    TRUE,
    TRUE
),
(
    'Event Distribution Policy',
    'publish_subscribe',
    5,
    TRUE,
    TRUE
);

-- ============================================================
-- MESSAGE CREATION
-- ============================================================

INSERT INTO communication_messages (
    sender_service_id,
    receiver_service_id,
    channel_id,
    method,
    idempotency_key,
    payload,
    status
)
SELECT
    sender.service_id,
    receiver.service_id,
    channel.channel_id,
    'synchronous',
    'PAYMENT-1001',
    '{"order_id":1001,"amount":2500,"currency":"INR"}'::jsonb,
    'delivered'
FROM communication_services sender
CROSS JOIN communication_services receiver
CROSS JOIN communication_channels channel
WHERE
    sender.service_name = 'checkout'
    AND receiver.service_name = 'payment'
    AND channel.channel_name = 'request_response_channel';

INSERT INTO communication_messages (
    sender_service_id,
    receiver_service_id,
    channel_id,
    method,
    idempotency_key,
    payload,
    status
)
SELECT
    sender.service_id,
    receiver.service_id,
    channel.channel_id,
    'asynchronous',
    'INVENTORY-1001',
    '{"order_id":1001,"operation":"reserve","quantity":5}'::jsonb,
    'queued'
FROM communication_services sender
CROSS JOIN communication_services receiver
CROSS JOIN communication_channels channel
WHERE
    sender.service_name = 'checkout'
    AND receiver.service_name = 'inventory'
    AND channel.channel_name = 'async_message_queue';

INSERT INTO communication_messages (
    sender_service_id,
    receiver_service_id,
    channel_id,
    method,
    topic_id,
    idempotency_key,
    payload,
    status
)
SELECT
    sender.service_id,
    NULL,
    channel.channel_id,
    'publish_subscribe',
    topic.topic_id,
    'ORDER-EVENT-1002',
    '{"order_id":1002,"event":"order.created"}'::jsonb,
    'queued'
FROM communication_services sender
CROSS JOIN communication_channels channel
CROSS JOIN communication_topics topic
WHERE
    sender.service_name = 'checkout'
    AND channel.channel_name = 'order_event_channel'
    AND topic.topic_name = 'order.created';

INSERT INTO communication_messages (
    sender_service_id,
    receiver_service_id,
    channel_id,
    method,
    idempotency_key,
    payload,
    status
)
SELECT
    sender.service_id,
    receiver.service_id,
    channel.channel_id,
    'webhook',
    'WEBHOOK-1003',
    '{"event":"order.shipped","order_id":1003}'::jsonb,
    'delivered'
FROM communication_services sender
CROSS JOIN communication_services receiver
CROSS JOIN communication_channels channel
WHERE
    sender.service_name = 'checkout'
    AND receiver.service_name = 'external_orders'
    AND channel.channel_name = 'webhook_channel';

-- ============================================================
-- DELIVERY INITIALIZATION
-- ============================================================

INSERT INTO communication_deliveries (
    message_id,
    receiver_service_id,
    status,
    attempt_number,
    delivered_at
)
SELECT
    m.message_id,
    m.receiver_service_id,
    'delivered',
    1,
    CURRENT_TIMESTAMP
FROM communication_messages m
WHERE m.method = 'synchronous';

INSERT INTO communication_deliveries (
    message_id,
    receiver_service_id,
    status,
    attempt_number
)
SELECT
    m.message_id,
    m.receiver_service_id,
    'pending',
    0
FROM communication_messages m
WHERE m.method = 'asynchronous';

INSERT INTO communication_deliveries (
    message_id,
    receiver_service_id,
    status,
    attempt_number,
    delivered_at
)
SELECT
    m.message_id,
    m.receiver_service_id,
    'delivered',
    1,
    CURRENT_TIMESTAMP
FROM communication_messages m
WHERE m.method = 'webhook';

-- ============================================================
-- DELIVERY ATTEMPT HISTORY
-- ============================================================

INSERT INTO communication_delivery_attempts (
    delivery_id,
    attempt_number,
    successful,
    error_message
)
SELECT
    delivery_id,
    1,
    status = 'delivered',
    CASE
        WHEN status = 'delivered' THEN NULL
        ELSE 'Initial delivery pending'
    END
FROM communication_deliveries;

-- ============================================================
-- STREAMING EXAMPLE
-- ============================================================

INSERT INTO communication_messages (
    sender_service_id,
    receiver_service_id,
    channel_id,
    method,
    idempotency_key,
    payload,
    status
)
SELECT
    sender.service_id,
    receiver.service_id,
    channel.channel_id,
    'streaming',
    'STREAM-1001',
    '{"stream":"monthly_report"}'::jsonb,
    'delivered'
FROM communication_services sender
CROSS JOIN communication_services receiver
CROSS JOIN communication_channels channel
WHERE
    sender.service_name = 'checkout'
    AND receiver.service_name = 'notifications'
    AND channel.channel_name = 'stream_channel';

INSERT INTO communication_stream_chunks (
    message_id,
    sequence_number,
    chunk_payload
)
SELECT
    message_id,
    0,
    'Monthly report '
FROM communication_messages
WHERE idempotency_key = 'STREAM-1001';

INSERT INTO communication_stream_chunks (
    message_id,
    sequence_number,
    chunk_payload
)
SELECT
    message_id,
    1,
    'processing completed'
FROM communication_messages
WHERE idempotency_key = 'STREAM-1001';

-- ============================================================
-- MESSAGE RETRIEVAL
-- ============================================================

CREATE OR REPLACE VIEW v_message_details AS
SELECT
    m.message_id,
    sender.service_name AS sender,
    receiver.service_name AS receiver,
    c.channel_name,
    m.method,
    m.status,
    m.priority,
    m.attempt_count,
    m.payload,
    m.created_at,
    m.delivered_at
FROM communication_messages m
JOIN communication_services sender
    ON sender.service_id = m.sender_service_id
LEFT JOIN communication_services receiver
    ON receiver.service_id = m.receiver_service_id
JOIN communication_channels c
    ON c.channel_id = m.channel_id;

-- ============================================================
-- DELIVERY REPORT
-- ============================================================

CREATE OR REPLACE VIEW v_delivery_report AS
SELECT
    method,
    status,
    COUNT(*) AS message_count,
    AVG(attempt_count) AS average_attempts
FROM communication_messages
GROUP BY method, status;

-- ============================================================
-- MESSAGE VALIDATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_message(
    p_message_id UUID
)
RETURNS TABLE (
    valid BOOLEAN,
    validation_message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_message communication_messages%ROWTYPE;
BEGIN
    SELECT *
    INTO v_message
    FROM communication_messages
    WHERE message_id = p_message_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT FALSE, 'Message does not exist';
        RETURN;
    END IF;

    IF v_message.status = 'dead_lettered' THEN
        RETURN QUERY
        SELECT FALSE, 'Message is in the dead-letter queue';
        RETURN;
    END IF;

    IF v_message.receiver_service_id IS NOT NULL
       AND NOT EXISTS (
           SELECT 1
           FROM communication_services
           WHERE service_id = v_message.receiver_service_id
             AND status = 'active'
       )
       AND v_message.method <> 'publish_subscribe'
    THEN
        RETURN QUERY
        SELECT FALSE, 'Receiver service is unavailable';
        RETURN;
    END IF;

    RETURN QUERY
    SELECT TRUE, 'Message validation passed';
END;
$$;

-- ============================================================
-- SUBSCRIBER DELIVERY INITIALIZATION
-- ============================================================

CREATE OR REPLACE FUNCTION initialize_topic_deliveries(
    p_message_id UUID
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_topic_id BIGINT;
    v_count INTEGER;
BEGIN
    SELECT topic_id
    INTO v_topic_id
    FROM communication_messages
    WHERE message_id = p_message_id
      AND method IN ('publish_subscribe', 'event_driven')
      AND status = 'queued';

    IF NOT FOUND OR v_topic_id IS NULL THEN
        RAISE EXCEPTION 'Invalid topic message';
    END IF;

    INSERT INTO communication_deliveries (
        message_id,
        receiver_service_id,
        status
    )
    SELECT
        p_message_id,
        subscription.service_id,
        'pending'
    FROM communication_subscriptions subscription
    JOIN communication_services service
        ON service.service_id = subscription.service_id
    WHERE subscription.topic_id = v_topic_id
      AND subscription.active = TRUE
      AND service.status = 'active'
    ON CONFLICT (message_id, receiver_service_id)
    DO NOTHING;

    GET DIAGNOSTICS v_count = ROW_COUNT;

    RETURN v_count;
END;
$$;

-- ============================================================
-- DELIVERY PROCESSING FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION process_delivery(
    p_delivery_id BIGINT,
    p_success BOOLEAN,
    p_error TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_delivery communication_deliveries%ROWTYPE;
    v_max_retries INTEGER;
    v_new_status delivery_status;
    v_message_status message_status;
BEGIN
    SELECT *
    INTO v_delivery
    FROM communication_deliveries
    WHERE delivery_id = p_delivery_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Delivery does not exist';
    END IF;

    IF v_delivery.status IN ('delivered', 'dead_lettered') THEN
        RAISE EXCEPTION 'Delivery is already terminal';
    END IF;

    SELECT channel.max_retries
    INTO v_max_retries
    FROM communication_messages message
    JOIN communication_channels channel
        ON channel.channel_id = message.channel_id
    WHERE message.message_id = v_delivery.message_id;

    UPDATE communication_deliveries
    SET
        attempt_number = attempt_number + 1,
        status = CASE
            WHEN p_success THEN 'delivered'::delivery_status
            WHEN attempt_number + 1 > v_max_retries
                THEN 'dead_lettered'::delivery_status
            ELSE 'failed'::delivery_status
        END,
        error_message = CASE
            WHEN p_success THEN NULL
            ELSE COALESCE(p_error, 'Delivery failed')
        END,
        delivered_at = CASE
            WHEN p_success THEN CURRENT_TIMESTAMP
            ELSE NULL
        END
    WHERE delivery_id = p_delivery_id
    RETURNING status INTO v_new_status;

    INSERT INTO communication_delivery_attempts (
        delivery_id,
        attempt_number,
        successful,
        error_message
    )
    VALUES (
        p_delivery_id,
        v_delivery.attempt_number + 1,
        p_success,
        p_error
    );

    IF v_new_status = 'dead_lettered' THEN
        INSERT INTO communication_dead_letters (
            delivery_id,
            failure_reason,
            original_payload
        )
        SELECT
            p_delivery_id,
            COALESCE(p_error, 'Maximum attempts exceeded'),
            message.payload
        FROM communication_messages message
        WHERE message.message_id = v_delivery.message_id;
    END IF;

    SELECT
        CASE
            WHEN COUNT(*) FILTER (
                WHERE status = 'delivered'
            ) = COUNT(*) THEN 'delivered'::message_status
            WHEN COUNT(*) FILTER (
                WHERE status = 'dead_lettered'
            ) > 0 THEN 'dead_lettered'::message_status
            ELSE 'processing'::message_status
        END
    INTO v_message_status
    FROM communication_deliveries
    WHERE message_id = v_delivery.message_id;

    UPDATE communication_messages
    SET
        status = v_message_status,
        attempt_count = (
            SELECT COALESCE(MAX(attempt_number), 0)
            FROM communication_deliveries
            WHERE message_id = v_delivery.message_id
        ),
        delivered_at = CASE
            WHEN v_message_status = 'delivered'
                THEN CURRENT_TIMESTAMP
            ELSE NULL
        END
    WHERE message_id = v_delivery.message_id;
END;
$$;

-- ============================================================
-- ELIGIBILITY REPORT FOR DELIVERY
-- ============================================================

CREATE OR REPLACE FUNCTION communication_eligibility(
    p_message_id UUID
)
RETURNS TABLE (
    eligible BOOLEAN,
    reason TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_method communication_method;
    v_status message_status;
    v_receiver BIGINT;
BEGIN
    SELECT method, status, receiver_service_id
    INTO v_method, v_status, v_receiver
    FROM communication_messages
    WHERE message_id = p_message_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT FALSE, 'Message not found';
        RETURN;
    END IF;

    IF v_status = 'delivered' THEN
        RETURN QUERY
        SELECT FALSE, 'Message already delivered';
        RETURN;
    END IF;

    IF v_status = 'dead_lettered' THEN
        RETURN QUERY
        SELECT FALSE, 'Message requires dead-letter recovery';
        RETURN;
    END IF;

    IF v_method NOT IN ('publish_subscribe', 'event_driven')
       AND NOT EXISTS (
           SELECT 1
           FROM communication_services
           WHERE service_id = v_receiver
             AND status = 'active'
       )
    THEN
        RETURN QUERY
        SELECT FALSE, 'Receiver is unavailable';
        RETURN;
    END IF;

    RETURN QUERY
    SELECT TRUE, 'Message is eligible for processing';
END;
$$;

-- ============================================================
-- STORED PROCEDURE: QUEUE MESSAGE
-- ============================================================

CREATE OR REPLACE PROCEDURE enqueue_message(
    p_sender BIGINT,
    p_receiver BIGINT,
    p_channel BIGINT,
    p_payload JSONB,
    p_idempotency_key TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_message_id UUID;
BEGIN
    IF jsonb_typeof(p_payload) <> 'object' THEN
        RAISE EXCEPTION 'Payload must be a JSON object';
    END IF;

    IF octet_length(p_payload::text) > 65536 THEN
        RAISE EXCEPTION 'Payload exceeds maximum size';
    END IF;

    INSERT INTO communication_messages (
        sender_service_id,
        receiver_service_id,
        channel_id,
        method,
        idempotency_key,
        payload,
        status
    )
    SELECT
        p_sender,
        p_receiver,
        p_channel,
        'asynchronous',
        p_idempotency_key,
        p_payload,
        'queued'
    WHERE EXISTS (
        SELECT 1
        FROM communication_services
        WHERE service_id = p_receiver
          AND status = 'active'
    )
    ON CONFLICT (sender_service_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL
    DO NOTHING
    RETURNING message_id INTO v_message_id;

    IF v_message_id IS NULL THEN
        RAISE NOTICE
            'Message was not inserted: duplicate key or inactive receiver';
        RETURN;
    END IF;

    INSERT INTO communication_deliveries (
        message_id,
        receiver_service_id,
        status
    )
    VALUES (
        v_message_id,
        p_receiver,
        'pending'
    );
END;
$$;

-- ============================================================
-- QUERY 1: MESSAGE RETRIEVAL
-- ============================================================

SELECT *
FROM v_message_details
ORDER BY created_at DESC;

-- ============================================================
-- QUERY 2: VALIDATION
-- ============================================================

SELECT
    message_id,
    (validate_message(message_id)).*
FROM communication_messages;

-- ============================================================
-- QUERY 3: DELIVERY AGGREGATION
-- ============================================================

SELECT
    method,
    status,
    COUNT(*) AS total_messages,
    ROUND(AVG(attempt_count), 2) AS average_attempts
FROM communication_messages
GROUP BY method, status
ORDER BY method, status;

-- ============================================================
-- QUERY 4: SERVICE COMMUNICATION VOLUME
-- ============================================================

SELECT
    service.service_name,
    COUNT(message.message_id) AS messages_sent
FROM communication_services service
LEFT JOIN communication_messages message
    ON message.sender_service_id = service.service_id
GROUP BY service.service_id, service.service_name
ORDER BY messages_sent DESC;

-- ============================================================
-- QUERY 5: SUBSCRIBER REPORT
-- ============================================================

SELECT
    topic.topic_name,
    service.service_name,
    subscription.active,
    subscription.subscribed_at
FROM communication_subscriptions subscription
JOIN communication_topics topic
    ON topic.topic_id = subscription.topic_id
JOIN communication_services service
    ON service.service_id = subscription.service_id
ORDER BY topic.topic_name, service.service_name;

-- ============================================================
-- QUERY 6: DELIVERY FAILURE ANALYSIS
-- ============================================================

SELECT
    service.service_name,
    COUNT(*) AS failed_deliveries,
    MAX(delivery.attempt_number) AS maximum_attempts
FROM communication_deliveries delivery
JOIN communication_services service
    ON service.service_id = delivery.receiver_service_id
WHERE delivery.status IN ('failed', 'dead_lettered')
GROUP BY service.service_name;

-- ============================================================
-- QUERY 7: MESSAGE ELIGIBILITY
-- ============================================================

SELECT
    message_id,
    communication_eligibility(message_id)
FROM communication_messages;

-- ============================================================
-- QUERY 8: STREAM RECONSTRUCTION
-- ============================================================

SELECT
    message_id,
    string_agg(chunk_payload, '' ORDER BY sequence_number)
        AS reconstructed_stream
FROM communication_stream_chunks
GROUP BY message_id;

-- ============================================================
-- QUERY 9: DEAD LETTER RETRIEVAL
-- ============================================================

SELECT
    dead_letter_id,
    delivery_id,
    failure_reason,
    original_payload,
    dead_lettered_at
FROM communication_dead_letters
WHERE replayed_at IS NULL
ORDER BY dead_lettered_at;

-- ============================================================
-- QUERY 10: STATUS AUDIT
-- ============================================================

SELECT
    message_id,
    previous_status,
    new_status,
    changed_at
FROM communication_status_audit
ORDER BY changed_at DESC;

-- ============================================================
-- TRANSACTIONAL DELIVERY EXAMPLE
--
-- Demonstrates atomic processing of one pending delivery.
-- A failed operation rolls back its state and attempt record.
-- ============================================================

DO $$
DECLARE
    v_delivery_id BIGINT;
BEGIN
    SELECT delivery_id
    INTO v_delivery_id
    FROM communication_deliveries
    WHERE status = 'pending'
    ORDER BY created_at
    LIMIT 1
    FOR UPDATE SKIP LOCKED;

    IF v_delivery_id IS NOT NULL THEN
        PERFORM process_delivery(
            v_delivery_id,
            TRUE,
            NULL
        );
    END IF;
END;
$$;

-- ============================================================
-- QUEUE PROCESSING PROCEDURE DEMONSTRATION
-- ============================================================

DO $$
DECLARE
    v_sender BIGINT;
    v_receiver BIGINT;
    v_channel BIGINT;
BEGIN
    SELECT service_id INTO v_sender
    FROM communication_services
    WHERE service_name = 'checkout';

    SELECT service_id INTO v_receiver
    FROM communication_services
    WHERE service_name = 'inventory';

    SELECT channel_id INTO v_channel
    FROM communication_channels
    WHERE channel_name = 'async_message_queue';

    CALL enqueue_message(
        v_sender,
        v_receiver,
        v_channel,
        '{"order_id":2001,"operation":"reserve"}'::jsonb,
        'INVENTORY-2001'
    );
END;
$$;

-- ============================================================
-- FINAL OPERATIONAL REPORT
-- ============================================================

SELECT
    channel_name,
    method,
    durable,
    max_retries
FROM communication_channels
ORDER BY channel_name;

SELECT *
FROM v_delivery_report
ORDER BY method, status;

COMMIT;
