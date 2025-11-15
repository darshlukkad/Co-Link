"""
Kafka producer utilities

Provides async Kafka producer for event publishing.
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional, Any, Dict
from enum import Enum

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

logger = logging.getLogger(__name__)

# Global Kafka producer
_kafka_producer: Optional[AIOKafkaProducer] = None


class EventType(str, Enum):
    """Kafka event types"""

    # Message events
    MESSAGE_SENT = "message.sent"
    MESSAGE_UPDATED = "message.updated"
    MESSAGE_DELETED = "message.deleted"

    # Thread events
    THREAD_CREATED = "thread.created"
    THREAD_REPLY_SENT = "thread.reply.sent"

    # Reaction events
    REACTION_ADDED = "reaction.added"
    REACTION_REMOVED = "reaction.removed"

    # Channel events
    CHANNEL_CREATED = "channel.created"
    CHANNEL_UPDATED = "channel.updated"
    CHANNEL_DELETED = "channel.deleted"
    CHANNEL_MEMBER_ADDED = "channel.member.added"
    CHANNEL_MEMBER_REMOVED = "channel.member.removed"

    # DM events
    DM_CREATED = "dm.created"

    # User events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_STATUS_CHANGED = "user.status.changed"

    # File events
    FILE_UPLOADED = "file.uploaded"
    FILE_DELETED = "file.deleted"


class KafkaTopic(str, Enum):
    """Kafka topics"""

    MESSAGES = "colink.messages"
    CHANNELS = "colink.channels"
    USERS = "colink.users"
    FILES = "colink.files"
    AUDIT = "colink.audit"


async def init_kafka_producer(
    bootstrap_servers: Optional[str] = None,
) -> AIOKafkaProducer:
    """
    Initialize Kafka producer

    Args:
        bootstrap_servers: Kafka bootstrap servers (defaults to KAFKA_BOOTSTRAP_SERVERS env var)

    Returns:
        AIOKafkaProducer instance
    """
    global _kafka_producer

    if _kafka_producer is not None:
        logger.warning("Kafka producer already initialized")
        return _kafka_producer

    # Get bootstrap servers
    servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

    logger.info(f"Initializing Kafka producer: {servers}")

    # Create producer
    _kafka_producer = AIOKafkaProducer(
        bootstrap_servers=servers,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        compression_type="gzip",
        acks="all",  # Wait for all replicas
        retries=3,
        max_in_flight_requests_per_connection=5,
    )

    # Start producer
    try:
        await _kafka_producer.start()
        logger.info("Kafka producer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to start Kafka producer: {e}")
        _kafka_producer = None
        raise

    return _kafka_producer


def get_kafka_producer() -> AIOKafkaProducer:
    """
    Get Kafka producer

    Returns:
        AIOKafkaProducer instance

    Raises:
        RuntimeError: If not initialized
    """
    if _kafka_producer is None:
        raise RuntimeError("Kafka producer not initialized. Call init_kafka_producer() first.")
    return _kafka_producer


async def close_kafka_producer():
    """Close Kafka producer"""
    global _kafka_producer

    if _kafka_producer:
        await _kafka_producer.stop()
        _kafka_producer = None
        logger.info("Kafka producer closed")


async def publish_event(
    topic: KafkaTopic,
    event_type: EventType,
    data: Dict[str, Any],
    key: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
) -> bool:
    """
    Publish event to Kafka

    Args:
        topic: Kafka topic
        event_type: Event type
        data: Event data
        key: Optional partition key (e.g., user_id, channel_id)
        headers: Optional message headers

    Returns:
        True if published successfully, False otherwise
    """
    producer = get_kafka_producer()

    # Build event payload
    event = {
        "event_type": event_type.value,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data,
    }

    # Convert key to bytes if provided
    key_bytes = key.encode("utf-8") if key else None

    # Convert headers to list of tuples
    headers_list = None
    if headers:
        headers_list = [(k, v.encode("utf-8")) for k, v in headers.items()]

    try:
        # Send message
        await producer.send(
            topic=topic.value,
            value=event,
            key=key_bytes,
            headers=headers_list,
        )

        logger.debug(f"Published event {event_type.value} to {topic.value}")
        return True

    except KafkaError as e:
        logger.error(f"Failed to publish event {event_type.value} to {topic.value}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error publishing event: {e}")
        return False


async def publish_message_event(
    event_type: EventType,
    message_id: str,
    channel_id: Optional[str] = None,
    dm_id: Optional[str] = None,
    user_id: Optional[str] = None,
    content: Optional[str] = None,
    **kwargs,
) -> bool:
    """
    Publish message-related event

    Args:
        event_type: Event type (MESSAGE_SENT, MESSAGE_UPDATED, MESSAGE_DELETED)
        message_id: Message ID
        channel_id: Channel ID (if applicable)
        dm_id: DM ID (if applicable)
        user_id: User ID who performed the action
        content: Message content (if applicable)
        **kwargs: Additional event data

    Returns:
        True if published successfully
    """
    data = {
        "message_id": message_id,
        "channel_id": channel_id,
        "dm_id": dm_id,
        "user_id": user_id,
        "content": content,
        **kwargs,
    }

    # Remove None values
    data = {k: v for k, v in data.items() if v is not None}

    # Use channel_id or dm_id as partition key for ordering
    key = channel_id or dm_id or message_id

    return await publish_event(
        topic=KafkaTopic.MESSAGES,
        event_type=event_type,
        data=data,
        key=key,
    )


async def publish_channel_event(
    event_type: EventType,
    channel_id: str,
    workspace_id: str,
    user_id: Optional[str] = None,
    **kwargs,
) -> bool:
    """
    Publish channel-related event

    Args:
        event_type: Event type (CHANNEL_CREATED, CHANNEL_UPDATED, etc.)
        channel_id: Channel ID
        workspace_id: Workspace ID
        user_id: User ID who performed the action
        **kwargs: Additional event data

    Returns:
        True if published successfully
    """
    data = {
        "channel_id": channel_id,
        "workspace_id": workspace_id,
        "user_id": user_id,
        **kwargs,
    }

    # Remove None values
    data = {k: v for k, v in data.items() if v is not None}

    return await publish_event(
        topic=KafkaTopic.CHANNELS,
        event_type=event_type,
        data=data,
        key=channel_id,
    )


async def publish_user_event(
    event_type: EventType,
    user_id: str,
    **kwargs,
) -> bool:
    """
    Publish user-related event

    Args:
        event_type: Event type (USER_CREATED, USER_UPDATED, etc.)
        user_id: User ID
        **kwargs: Additional event data

    Returns:
        True if published successfully
    """
    data = {
        "user_id": user_id,
        **kwargs,
    }

    return await publish_event(
        topic=KafkaTopic.USERS,
        event_type=event_type,
        data=data,
        key=user_id,
    )


async def publish_audit_event(
    action: str,
    resource_type: str,
    resource_id: str,
    user_id: str,
    workspace_id: str,
    details: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Publish audit log event

    Args:
        action: Action performed (create, update, delete, etc.)
        resource_type: Type of resource (message, channel, user, etc.)
        resource_id: Resource ID
        user_id: User ID who performed the action
        workspace_id: Workspace ID
        details: Additional details

    Returns:
        True if published successfully
    """
    data = {
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "user_id": user_id,
        "workspace_id": workspace_id,
        "details": details or {},
    }

    return await publish_event(
        topic=KafkaTopic.AUDIT,
        event_type=EventType.MESSAGE_SENT,  # Generic event type for audit
        data=data,
        key=resource_id,
    )
