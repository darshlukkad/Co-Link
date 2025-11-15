"""
CoLink Common Database Module

Shared database utilities for all CoLink services.
"""

from .postgres import (
    get_postgres_engine,
    get_postgres_session,
    init_postgres,
)
from .mongodb import (
    get_mongodb_client,
    get_mongodb_database,
    init_mongodb,
)
from .redis_client import (
    get_redis_client,
    init_redis,
)
from .kafka_producer import (
    get_kafka_producer,
    init_kafka_producer,
    close_kafka_producer,
    publish_event,
    publish_message_event,
    publish_channel_event,
    publish_user_event,
    publish_audit_event,
    EventType,
    KafkaTopic,
)

__all__ = [
    "get_postgres_engine",
    "get_postgres_session",
    "init_postgres",
    "get_mongodb_client",
    "get_mongodb_database",
    "init_mongodb",
    "get_redis_client",
    "init_redis",
    "get_kafka_producer",
    "init_kafka_producer",
    "close_kafka_producer",
    "publish_event",
    "publish_message_event",
    "publish_channel_event",
    "publish_user_event",
    "publish_audit_event",
    "EventType",
    "KafkaTopic",
]
