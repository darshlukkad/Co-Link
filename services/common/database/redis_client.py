"""
Redis connection utilities

Provides Redis client for caching, sessions, and pub/sub.
"""

import logging
import os
from typing import Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

# Global Redis client
_redis_client: Optional[Redis] = None


async def init_redis(
    redis_url: Optional[str] = None,
    max_connections: int = 50,
) -> Redis:
    """
    Initialize Redis connection

    Args:
        redis_url: Redis connection URL (defaults to REDIS_URL env var)
        max_connections: Maximum connections in pool

    Returns:
        Redis client
    """
    global _redis_client

    if _redis_client is not None:
        logger.warning("Redis already initialized")
        return _redis_client

    # Get connection URL
    url = redis_url or os.getenv("REDIS_URL")
    if not url:
        raise ValueError("REDIS_URL not set")

    logger.info("Initializing Redis connection")

    # Create client with connection pool
    _redis_client = await aioredis.from_url(
        url,
        max_connections=max_connections,
        decode_responses=True,  # Auto-decode bytes to strings
        encoding="utf-8",
    )

    # Verify connection
    try:
        await _redis_client.ping()
        logger.info("Redis initialized successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        _redis_client = None
        raise

    return _redis_client


def get_redis_client() -> Redis:
    """
    Get Redis client

    Returns:
        Redis client

    Raises:
        RuntimeError: If not initialized
    """
    if _redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis_client


async def close_redis():
    """Close Redis connection"""
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")
