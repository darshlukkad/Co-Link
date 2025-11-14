"""
MongoDB connection utilities

Provides MongoDB client and database access.
"""

import logging
import os
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database

logger = logging.getLogger(__name__)

# Global MongoDB client
_mongo_client: Optional[MongoClient] = None
_mongo_database: Optional[Database] = None


def init_mongodb(
    mongodb_url: Optional[str] = None,
    database_name: Optional[str] = None,
) -> MongoClient:
    """
    Initialize MongoDB connection

    Args:
        mongodb_url: MongoDB connection URL (defaults to MONGODB_URL env var)
        database_name: Database name (defaults to MONGODB_DATABASE env var)

    Returns:
        MongoDB client
    """
    global _mongo_client, _mongo_database

    if _mongo_client is not None:
        logger.warning("MongoDB already initialized")
        return _mongo_client

    # Get connection URL
    url = mongodb_url or os.getenv("MONGODB_URL")
    if not url:
        raise ValueError("MONGODB_URL not set")

    # Get database name
    db_name = database_name or os.getenv("MONGODB_DATABASE", "colink")

    logger.info(f"Initializing MongoDB connection to database: {db_name}")

    # Create client
    _mongo_client = MongoClient(
        url,
        maxPoolSize=50,
        minPoolSize=10,
        serverSelectionTimeoutMS=5000,
    )

    # Get database
    _mongo_database = _mongo_client[db_name]

    # Verify connection
    try:
        _mongo_client.server_info()
        logger.info("MongoDB initialized successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        _mongo_client = None
        _mongo_database = None
        raise

    return _mongo_client


def get_mongodb_client() -> MongoClient:
    """
    Get MongoDB client

    Returns:
        MongoDB client

    Raises:
        RuntimeError: If not initialized
    """
    if _mongo_client is None:
        raise RuntimeError("MongoDB not initialized. Call init_mongodb() first.")
    return _mongo_client


def get_mongodb_database() -> Database:
    """
    Get MongoDB database

    Returns:
        MongoDB database

    Raises:
        RuntimeError: If not initialized
    """
    if _mongo_database is None:
        raise RuntimeError("MongoDB not initialized. Call init_mongodb() first.")
    return _mongo_database


def close_mongodb():
    """Close MongoDB connection"""
    global _mongo_client, _mongo_database

    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _mongo_database = None
        logger.info("MongoDB connection closed")
