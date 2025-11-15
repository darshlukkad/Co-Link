"""
Search Service business logic

Handles full-text search for messages (PostgreSQL) and files (MongoDB).
"""

import logging
from datetime import datetime
from typing import Optional, List, Tuple

from sqlalchemy import select, and_, func, text
from sqlalchemy.orm import Session
from motor.motor_asyncio import AsyncIOMotorDatabase

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# Import message model from messaging service
from messaging.app.database import Message

logger = logging.getLogger(__name__)


class MessageSearchService:
    """Service for message full-text search"""

    @staticmethod
    def search_messages(
        db: Session,
        query: str,
        channel_id: Optional[str] = None,
        user_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Message], int]:
        """
        Search messages using PostgreSQL full-text search

        Args:
            query: Search query
            channel_id: Filter by channel
            user_id: Filter by user
            from_date: Filter by start date
            to_date: Filter by end date
            limit: Results per page
            offset: Pagination offset

        Returns:
            Tuple of (messages, total_count)
        """
        # Build base query
        # Use PostgreSQL to_tsvector and to_tsquery for full-text search
        search_query = select(Message).where(
            and_(
                Message.is_deleted == False,
                # Full-text search on content
                text("to_tsvector('english', content) @@ plainto_tsquery('english', :query)")
            )
        ).params(query=query)

        # Apply filters
        if channel_id:
            from uuid import UUID
            search_query = search_query.where(Message.channel_id == UUID(channel_id))

        if user_id:
            search_query = search_query.where(Message.user_id == user_id)

        if from_date:
            search_query = search_query.where(Message.created_at >= from_date)

        if to_date:
            search_query = search_query.where(Message.created_at <= to_date)

        # Get total count
        count_query = select(func.count()).select_from(search_query.subquery())
        total = db.execute(count_query).scalar() or 0

        # Add relevance score using ts_rank
        search_query = search_query.add_columns(
            text("ts_rank(to_tsvector('english', content), plainto_tsquery('english', :query)) as relevance")
        ).params(query=query)

        # Order by relevance and recency
        search_query = search_query.order_by(
            text("relevance DESC"),
            Message.created_at.desc()
        )

        # Apply pagination
        search_query = search_query.limit(limit).offset(offset)

        # Execute query
        results = db.execute(search_query).all()

        # Extract messages (first element of each result tuple)
        messages = [result[0] for result in results]

        return messages, total

    @staticmethod
    def generate_snippet(content: str, query: str, max_length: int = 200) -> str:
        """
        Generate a snippet with query highlighted

        Args:
            content: Full message content
            query: Search query
            max_length: Maximum snippet length

        Returns:
            Content snippet
        """
        query_lower = query.lower()
        content_lower = content.lower()

        # Find query position
        pos = content_lower.find(query_lower)

        if pos == -1:
            # Query not found, return beginning
            return content[:max_length] + ("..." if len(content) > max_length else "")

        # Calculate snippet bounds
        start = max(0, pos - 50)
        end = min(len(content), pos + len(query) + 150)

        snippet = content[start:end]

        # Add ellipsis
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet


class FileSearchService:
    """Service for file metadata search"""

    @staticmethod
    async def search_files(
        db: AsyncIOMotorDatabase,
        query: str,
        channel_id: Optional[str] = None,
        content_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[dict], int]:
        """
        Search file metadata using MongoDB text search

        Args:
            query: Search query
            channel_id: Filter by channel
            content_type: Filter by content type
            limit: Results per page
            offset: Pagination offset

        Returns:
            Tuple of (files, total_count)
        """
        # Build MongoDB query
        mongo_query = {
            "$text": {"$search": query},
            "deleted_at": {"$exists": False},
            "uploaded_at": {"$exists": True, "$ne": None},
        }

        # Apply filters
        if channel_id:
            mongo_query["channel_id"] = channel_id

        if content_type:
            mongo_query["content_type"] = {"$regex": f"^{content_type}", "$options": "i"}

        # Get total count
        total = await db.files.count_documents(mongo_query)

        # Search with relevance score
        cursor = db.files.find(
            mongo_query,
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).skip(offset).limit(limit)

        files = await cursor.to_list(length=limit)

        return files, total


class UnifiedSearchService:
    """Service for unified search across messages and files"""

    @staticmethod
    async def unified_search(
        pg_db: Session,
        mongo_db: AsyncIOMotorDatabase,
        query: str,
        limit: int = 20,
    ) -> Tuple[List[Message], List[dict], int, int]:
        """
        Search both messages and files

        Args:
            pg_db: PostgreSQL database session
            mongo_db: MongoDB database
            query: Search query
            limit: Results per search type

        Returns:
            Tuple of (messages, files, total_messages, total_files)
        """
        # Search messages
        messages, total_messages = MessageSearchService.search_messages(
            db=pg_db,
            query=query,
            limit=limit,
            offset=0,
        )

        # Search files
        files, total_files = await FileSearchService.search_files(
            db=mongo_db,
            query=query,
            limit=limit,
            offset=0,
        )

        return messages, files, total_messages, total_files
