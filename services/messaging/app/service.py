"""
Messaging Service business logic

Handles database operations and Kafka event publishing for messages,
threads, and reactions.
"""

import logging
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from common.database import (
    publish_message_event,
    publish_audit_event,
    EventType,
)
from .database import Message, Thread, ThreadMessage, Reaction
from .models import (
    CreateMessageRequest,
    UpdateMessageRequest,
    CreateThreadReplyRequest,
    AddReactionRequest,
)

logger = logging.getLogger(__name__)


class MessageService:
    """Service for message operations"""

    @staticmethod
    async def create_message(
        db: Session,
        channel_id: Optional[str],
        dm_id: Optional[str],
        user_id: str,
        request: CreateMessageRequest,
    ) -> Message:
        """Create a new message"""
        message = Message(
            message_id=uuid4(),
            channel_id=UUID(channel_id) if channel_id else None,
            dm_id=UUID(dm_id) if dm_id else None,
            user_id=user_id,
            content=request.content,
            created_at=datetime.utcnow(),
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        # Publish Kafka event
        await publish_message_event(
            event_type=EventType.MESSAGE_SENT,
            message_id=str(message.message_id),
            channel_id=channel_id,
            dm_id=dm_id,
            user_id=user_id,
            content=request.content,
            mentions=request.mentions,
            attachments=request.attachments,
        )

        logger.info(f"Message {message.message_id} created by user {user_id}")
        return message

    @staticmethod
    def get_messages(
        db: Session,
        channel_id: Optional[str] = None,
        dm_id: Optional[str] = None,
        limit: int = 50,
        before: Optional[str] = None,
        after: Optional[str] = None,
    ) -> Tuple[List[Message], bool]:
        """Get paginated messages"""
        query = select(Message).where(Message.is_deleted == False)

        if channel_id:
            query = query.where(Message.channel_id == UUID(channel_id))
        if dm_id:
            query = query.where(Message.dm_id == UUID(dm_id))

        # Pagination
        if before:
            query = query.where(Message.message_id < UUID(before))
        if after:
            query = query.where(Message.message_id > UUID(after))

        # Order by created_at descending (newest first)
        query = query.order_by(desc(Message.created_at)).limit(limit + 1)

        messages = db.execute(query).scalars().all()

        # Check if there are more results
        has_more = len(messages) > limit
        if has_more:
            messages = messages[:limit]

        return messages, has_more

    @staticmethod
    def get_message(db: Session, message_id: str) -> Optional[Message]:
        """Get a single message by ID"""
        query = select(Message).where(
            and_(
                Message.message_id == UUID(message_id),
                Message.is_deleted == False,
            )
        )
        return db.execute(query).scalar_one_or_none()

    @staticmethod
    async def update_message(
        db: Session,
        message_id: str,
        user_id: str,
        request: UpdateMessageRequest,
    ) -> Optional[Message]:
        """Update a message (author only)"""
        message = MessageService.get_message(db, message_id)
        if not message:
            return None

        # Verify ownership
        if message.user_id != user_id:
            raise PermissionError("Only the message author can edit this message")

        # Update content
        message.content = request.content
        message.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(message)

        # Publish Kafka event
        await publish_message_event(
            event_type=EventType.MESSAGE_UPDATED,
            message_id=str(message.message_id),
            channel_id=str(message.channel_id) if message.channel_id else None,
            dm_id=str(message.dm_id) if message.dm_id else None,
            user_id=user_id,
            content=request.content,
        )

        logger.info(f"Message {message_id} updated by user {user_id}")
        return message

    @staticmethod
    async def delete_message(
        db: Session,
        message_id: str,
        user_id: str,
        is_admin: bool = False,
    ) -> bool:
        """Soft delete a message"""
        message = MessageService.get_message(db, message_id)
        if not message:
            return False

        # Verify ownership or admin
        if message.user_id != user_id and not is_admin:
            raise PermissionError("Only the message author or admin can delete this message")

        # Soft delete
        message.is_deleted = True
        message.deleted_at = datetime.utcnow()

        db.commit()

        # Publish Kafka event
        await publish_message_event(
            event_type=EventType.MESSAGE_DELETED,
            message_id=str(message.message_id),
            channel_id=str(message.channel_id) if message.channel_id else None,
            dm_id=str(message.dm_id) if message.dm_id else None,
            user_id=user_id,
        )

        logger.info(f"Message {message_id} deleted by user {user_id}")
        return True


class ThreadService:
    """Service for thread/reply operations"""

    @staticmethod
    async def create_thread_reply(
        db: Session,
        message_id: str,
        user_id: str,
        request: CreateThreadReplyRequest,
    ) -> Optional[ThreadMessage]:
        """Create a reply to a message thread"""
        # Verify parent message exists
        parent_message = MessageService.get_message(db, message_id)
        if not parent_message:
            return None

        # Get or create thread
        thread_query = select(Thread).where(Thread.message_id == UUID(message_id))
        thread = db.execute(thread_query).scalar_one_or_none()

        if not thread:
            thread = Thread(
                thread_id=uuid4(),
                message_id=UUID(message_id),
                reply_count=0,
                created_at=datetime.utcnow(),
            )
            db.add(thread)
            db.flush()

        # Create thread message
        thread_message = ThreadMessage(
            reply_id=uuid4(),
            thread_id=thread.thread_id,
            user_id=user_id,
            content=request.content,
            created_at=datetime.utcnow(),
        )

        db.add(thread_message)

        # Update thread stats
        thread.reply_count += 1
        thread.last_reply_at = datetime.utcnow()

        db.commit()
        db.refresh(thread_message)

        # Publish Kafka event
        await publish_message_event(
            event_type=EventType.THREAD_REPLY_SENT,
            message_id=str(thread_message.reply_id),
            channel_id=str(parent_message.channel_id) if parent_message.channel_id else None,
            user_id=user_id,
            content=request.content,
            parent_message_id=message_id,
            thread_id=str(thread.thread_id),
        )

        logger.info(f"Thread reply {thread_message.reply_id} created by user {user_id}")
        return thread_message

    @staticmethod
    def get_thread_replies(
        db: Session,
        message_id: str,
        limit: int = 50,
        after: Optional[str] = None,
    ) -> Tuple[List[ThreadMessage], int, bool]:
        """Get thread replies"""
        # Get thread
        thread_query = select(Thread).where(Thread.message_id == UUID(message_id))
        thread = db.execute(thread_query).scalar_one_or_none()

        if not thread:
            return [], 0, False

        # Get replies
        query = select(ThreadMessage).where(
            and_(
                ThreadMessage.thread_id == thread.thread_id,
                ThreadMessage.is_deleted == False,
            )
        )

        if after:
            query = query.where(ThreadMessage.reply_id > UUID(after))

        query = query.order_by(ThreadMessage.created_at).limit(limit + 1)

        replies = db.execute(query).scalars().all()

        # Check if there are more results
        has_more = len(replies) > limit
        if has_more:
            replies = replies[:limit]

        return replies, thread.reply_count, has_more


class ReactionService:
    """Service for reaction operations"""

    @staticmethod
    async def add_reaction(
        db: Session,
        message_id: str,
        user_id: str,
        request: AddReactionRequest,
    ) -> Optional[Reaction]:
        """Add a reaction to a message"""
        # Verify message exists
        message = MessageService.get_message(db, message_id)
        if not message:
            return None

        # Create reaction
        reaction = Reaction(
            reaction_id=uuid4(),
            message_id=UUID(message_id),
            user_id=user_id,
            emoji=request.emoji,
            created_at=datetime.utcnow(),
        )

        try:
            db.add(reaction)
            db.commit()
            db.refresh(reaction)
        except IntegrityError:
            # Duplicate reaction (unique constraint violation)
            db.rollback()
            raise ValueError("Reaction already exists")

        # Publish Kafka event
        await publish_message_event(
            event_type=EventType.REACTION_ADDED,
            message_id=message_id,
            channel_id=str(message.channel_id) if message.channel_id else None,
            dm_id=str(message.dm_id) if message.dm_id else None,
            user_id=user_id,
            emoji=request.emoji,
            reaction_id=str(reaction.reaction_id),
        )

        logger.info(f"Reaction {reaction.reaction_id} added by user {user_id}")
        return reaction

    @staticmethod
    def get_reactions(db: Session, message_id: str) -> List[Reaction]:
        """Get all reactions for a message"""
        query = select(Reaction).where(Reaction.message_id == UUID(message_id))
        query = query.order_by(Reaction.created_at)
        return db.execute(query).scalars().all()

    @staticmethod
    async def remove_reaction(
        db: Session,
        reaction_id: str,
        user_id: str,
    ) -> bool:
        """Remove a reaction"""
        query = select(Reaction).where(Reaction.reaction_id == UUID(reaction_id))
        reaction = db.execute(query).scalar_one_or_none()

        if not reaction:
            return False

        # Verify ownership
        if reaction.user_id != user_id:
            raise PermissionError("Only the user who added the reaction can remove it")

        # Get message for event publishing
        message = MessageService.get_message(db, str(reaction.message_id))

        db.delete(reaction)
        db.commit()

        # Publish Kafka event
        if message:
            await publish_message_event(
                event_type=EventType.REACTION_REMOVED,
                message_id=str(reaction.message_id),
                channel_id=str(message.channel_id) if message.channel_id else None,
                dm_id=str(message.dm_id) if message.dm_id else None,
                user_id=user_id,
                emoji=reaction.emoji,
                reaction_id=reaction_id,
            )

        logger.info(f"Reaction {reaction_id} removed by user {user_id}")
        return True
