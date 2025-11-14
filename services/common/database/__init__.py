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

__all__ = [
    "get_postgres_engine",
    "get_postgres_session",
    "init_postgres",
    "get_mongodb_client",
    "get_mongodb_database",
    "init_mongodb",
    "get_redis_client",
    "init_redis",
]
