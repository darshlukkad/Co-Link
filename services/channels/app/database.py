"""
Database models for Channels Service

SQLAlchemy models for channels, members, and direct messages.
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
    UniqueConstraint,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import relationship
import enum

import sys
import os

# Add common module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../common"))

from database.postgres import Base


class MemberRole(str, enum.Enum):
    """Channel member roles"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Channel(Base):
    """Channel model"""

    __tablename__ = "channels"

    channel_id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()")
    workspace_id = Column(PGUUID(as_uuid=True), nullable=False)  # Will be linked to workspaces table
    name = Column(String(80), nullable=False)
    description = Column(String(250), nullable=True)
    is_private = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    created_by = Column(String(255), nullable=False)  # Keycloak user ID
    created_at = Column(DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    members = relationship("ChannelMember", back_populates="channel", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_channels_workspace_id", "workspace_id"),
        Index("idx_channels_name", "name"),
        Index("idx_channels_created_by", "created_by"),
        # Unique channel name per workspace
        UniqueConstraint("workspace_id", "name", name="uq_channels_workspace_name"),
    )


class ChannelMember(Base):
    """Channel membership model"""

    __tablename__ = "channel_members"

    channel_id = Column(PGUUID(as_uuid=True), ForeignKey("channels.channel_id"), primary_key=True)
    user_id = Column(String(255), primary_key=True)  # Keycloak user ID
    role = Column(Enum(MemberRole), nullable=False, default=MemberRole.MEMBER)
    joined_at = Column(DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP")

    # Relationships
    channel = relationship("Channel", back_populates="members")

    __table_args__ = (
        Index("idx_channel_members_user_id", "user_id"),
        Index("idx_channel_members_channel_id", "channel_id"),
    )


class DirectMessage(Base):
    """Direct message session model"""

    __tablename__ = "direct_messages"

    dm_id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="uuid_generate_v4()")
    workspace_id = Column(PGUUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP")

    # Relationships
    participants = relationship("DMParticipant", back_populates="dm", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_direct_messages_workspace_id", "workspace_id"),
    )


class DMParticipant(Base):
    """Direct message participant model"""

    __tablename__ = "dm_participants"

    dm_id = Column(PGUUID(as_uuid=True), ForeignKey("direct_messages.dm_id"), primary_key=True)
    user_id = Column(String(255), primary_key=True)  # Keycloak user ID
    joined_at = Column(DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP")

    # Relationships
    dm = relationship("DirectMessage", back_populates="participants")

    __table_args__ = (
        Index("idx_dm_participants_user_id", "user_id"),
        Index("idx_dm_participants_dm_id", "dm_id"),
    )
