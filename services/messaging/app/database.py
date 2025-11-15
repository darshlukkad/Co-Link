"""
Database models for Messaging Service

SQLAlchemy models matching the PostgreSQL schema.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Integer,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

import sys
import os

# Add common module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../common"))

from database.postgres import Base


class Message(Base):
    """Message model"""

    __tablename__ = "messages"

    message_id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()")
    channel_id = Column(PGUUID(as_uuid=True), ForeignKey("channels.channel_id"), nullable=True)
    dm_id = Column(PGUUID(as_uuid=True), ForeignKey("direct_messages.dm_id"), nullable=True)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Relationships
    reactions = relationship("Reaction", back_populates="message", cascade="all, delete-orphan")
    thread = relationship("Thread", back_populates="message", uselist=False)

    __table_args__ = (
        Index("idx_messages_channel_id", "channel_id"),
        Index("idx_messages_dm_id", "dm_id"),
        Index("idx_messages_user_id", "user_id"),
        Index("idx_messages_created_at", "created_at"),
    )


class Thread(Base):
    """Thread model"""

    __tablename__ = "threads"

    thread_id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()")
    message_id = Column(PGUUID(as_uuid=True), ForeignKey("messages.message_id"), unique=True, nullable=False)
    reply_count = Column(Integer, default=0, nullable=False)
    last_reply_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP")

    # Relationships
    message = relationship("Message", back_populates="thread")
    replies = relationship("ThreadMessage", back_populates="thread", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_threads_message_id", "message_id"),
        Index("idx_threads_last_reply_at", "last_reply_at"),
    )


class ThreadMessage(Base):
    """Thread message (reply) model"""

    __tablename__ = "thread_messages"

    reply_id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()")
    thread_id = Column(PGUUID(as_uuid=True), ForeignKey("threads.thread_id"), nullable=False)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Relationships
    thread = relationship("Thread", back_populates="replies")

    __table_args__ = (
        Index("idx_thread_messages_thread_id", "thread_id"),
        Index("idx_thread_messages_user_id", "user_id"),
        Index("idx_thread_messages_created_at", "created_at"),
    )


class Reaction(Base):
    """Reaction model"""

    __tablename__ = "reactions"

    reaction_id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()")
    message_id = Column(PGUUID(as_uuid=True), ForeignKey("messages.message_id"), nullable=False)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    emoji = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP")

    # Relationships
    message = relationship("Message", back_populates="reactions")

    __table_args__ = (
        Index("idx_reactions_message_id", "message_id"),
        Index("idx_reactions_user_id", "user_id"),
        # Unique constraint: one user can only add the same emoji once per message
        Index("idx_reactions_unique", "message_id", "user_id", "emoji", unique=True),
    )
