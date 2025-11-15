"""
Channels Service business logic

Handles database operations and Kafka event publishing for channels,
members, and direct messages.
"""

import logging
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from common.database import (
    publish_channel_event,
    EventType,
)
from .database import Channel, ChannelMember, DirectMessage, DMParticipant, MemberRole
from .models import (
    CreateChannelRequest,
    UpdateChannelRequest,
    CreateDMRequest,
    AddMemberRequest,
)

logger = logging.getLogger(__name__)


class ChannelService:
    """Service for channel operations"""

    @staticmethod
    async def create_channel(
        db: Session,
        workspace_id: str,
        user_id: str,
        request: CreateChannelRequest,
    ) -> Channel:
        """Create a new channel"""
        channel = Channel(
            channel_id=uuid4(),
            workspace_id=UUID(workspace_id),
            name=request.name,
            description=request.description,
            is_private=request.is_private,
            created_by=user_id,
            created_at=datetime.utcnow(),
        )

        db.add(channel)

        # Add creator as owner
        member = ChannelMember(
            channel_id=channel.channel_id,
            user_id=user_id,
            role=MemberRole.OWNER,
            joined_at=datetime.utcnow(),
        )
        db.add(member)

        try:
            db.commit()
            db.refresh(channel)
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Channel with name '{request.name}' already exists in this workspace")

        # Publish Kafka event
        await publish_channel_event(
            event_type=EventType.CHANNEL_CREATED,
            channel_id=str(channel.channel_id),
            workspace_id=workspace_id,
            user_id=user_id,
            name=request.name,
            is_private=request.is_private,
        )

        logger.info(f"Channel {channel.channel_id} created by user {user_id}")
        return channel

    @staticmethod
    def get_channels(
        db: Session,
        workspace_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        include_private: bool = False,
    ) -> Tuple[List[Channel], int]:
        """Get channels in a workspace"""
        query = select(Channel).where(
            and_(
                Channel.workspace_id == UUID(workspace_id),
                Channel.is_archived == False,
            )
        )

        # Filter private channels unless user is a member
        if not include_private:
            # Get user's channel memberships
            member_query = select(ChannelMember.channel_id).where(
                ChannelMember.user_id == user_id
            )
            member_channel_ids = db.execute(member_query).scalars().all()

            # Include public channels + user's private channels
            query = query.where(
                or_(
                    Channel.is_private == False,
                    Channel.channel_id.in_(member_channel_ids)
                )
            )

        # Get total count
        total_query = select(func.count()).select_from(query.subquery())
        total = db.execute(total_query).scalar()

        # Get paginated results
        query = query.order_by(Channel.created_at.desc()).limit(limit).offset(offset)
        channels = db.execute(query).scalars().all()

        return channels, total

    @staticmethod
    def get_channel(
        db: Session,
        channel_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[Channel]:
        """Get a single channel by ID"""
        query = select(Channel).where(
            and_(
                Channel.channel_id == UUID(channel_id),
                Channel.is_archived == False,
            )
        )
        channel = db.execute(query).scalar_one_or_none()

        if not channel:
            return None

        # Check access for private channels
        if channel.is_private and user_id:
            member_query = select(ChannelMember).where(
                and_(
                    ChannelMember.channel_id == UUID(channel_id),
                    ChannelMember.user_id == user_id,
                )
            )
            member = db.execute(member_query).scalar_one_or_none()
            if not member:
                raise PermissionError("You do not have access to this private channel")

        return channel

    @staticmethod
    async def update_channel(
        db: Session,
        channel_id: str,
        user_id: str,
        request: UpdateChannelRequest,
    ) -> Optional[Channel]:
        """Update a channel (admin/owner only)"""
        channel = ChannelService.get_channel(db, channel_id)
        if not channel:
            return None

        # Verify user is admin or owner
        member_query = select(ChannelMember).where(
            and_(
                ChannelMember.channel_id == UUID(channel_id),
                ChannelMember.user_id == user_id,
            )
        )
        member = db.execute(member_query).scalar_one_or_none()

        if not member or member.role not in [MemberRole.OWNER, MemberRole.ADMIN]:
            raise PermissionError("Only channel owners or admins can update the channel")

        # Update fields
        if request.name is not None:
            channel.name = request.name
        if request.description is not None:
            channel.description = request.description

        channel.updated_at = datetime.utcnow()

        try:
            db.commit()
            db.refresh(channel)
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Channel with name '{request.name}' already exists in this workspace")

        # Publish Kafka event
        await publish_channel_event(
            event_type=EventType.CHANNEL_UPDATED,
            channel_id=str(channel.channel_id),
            workspace_id=str(channel.workspace_id),
            user_id=user_id,
            name=channel.name,
        )

        logger.info(f"Channel {channel_id} updated by user {user_id}")
        return channel

    @staticmethod
    async def archive_channel(
        db: Session,
        channel_id: str,
        user_id: str,
    ) -> bool:
        """Archive a channel (owner only)"""
        channel = ChannelService.get_channel(db, channel_id)
        if not channel:
            return False

        # Verify user is owner
        member_query = select(ChannelMember).where(
            and_(
                ChannelMember.channel_id == UUID(channel_id),
                ChannelMember.user_id == user_id,
            )
        )
        member = db.execute(member_query).scalar_one_or_none()

        if not member or member.role != MemberRole.OWNER:
            raise PermissionError("Only channel owners can archive the channel")

        # Archive channel
        channel.is_archived = True
        channel.updated_at = datetime.utcnow()

        db.commit()

        # Publish Kafka event
        await publish_channel_event(
            event_type=EventType.CHANNEL_DELETED,
            channel_id=str(channel.channel_id),
            workspace_id=str(channel.workspace_id),
            user_id=user_id,
        )

        logger.info(f"Channel {channel_id} archived by user {user_id}")
        return True

    @staticmethod
    def get_member_count(db: Session, channel_id: str) -> int:
        """Get member count for a channel"""
        query = select(func.count()).select_from(ChannelMember).where(
            ChannelMember.channel_id == UUID(channel_id)
        )
        return db.execute(query).scalar() or 0


class MemberService:
    """Service for channel membership operations"""

    @staticmethod
    async def add_member(
        db: Session,
        channel_id: str,
        requester_id: str,
        request: AddMemberRequest,
    ) -> Optional[ChannelMember]:
        """Add a member to a channel"""
        # Verify channel exists
        channel = ChannelService.get_channel(db, channel_id)
        if not channel:
            return None

        # Verify requester is admin or owner (for private channels)
        if channel.is_private:
            requester_query = select(ChannelMember).where(
                and_(
                    ChannelMember.channel_id == UUID(channel_id),
                    ChannelMember.user_id == requester_id,
                )
            )
            requester_member = db.execute(requester_query).scalar_one_or_none()

            if not requester_member or requester_member.role not in [MemberRole.OWNER, MemberRole.ADMIN]:
                raise PermissionError("Only channel owners or admins can add members to private channels")

        # Create membership
        member = ChannelMember(
            channel_id=UUID(channel_id),
            user_id=request.user_id,
            role=MemberRole[request.role.upper()],
            joined_at=datetime.utcnow(),
        )

        try:
            db.add(member)
            db.commit()
            db.refresh(member)
        except IntegrityError:
            db.rollback()
            raise ValueError("User is already a member of this channel")

        # Publish Kafka event
        await publish_channel_event(
            event_type=EventType.CHANNEL_MEMBER_ADDED,
            channel_id=channel_id,
            workspace_id=str(channel.workspace_id),
            user_id=request.user_id,
            added_by=requester_id,
        )

        logger.info(f"User {request.user_id} added to channel {channel_id} by {requester_id}")
        return member

    @staticmethod
    def get_members(db: Session, channel_id: str) -> List[ChannelMember]:
        """Get all members of a channel"""
        query = select(ChannelMember).where(
            ChannelMember.channel_id == UUID(channel_id)
        )
        query = query.order_by(ChannelMember.joined_at)
        return db.execute(query).scalars().all()

    @staticmethod
    async def remove_member(
        db: Session,
        channel_id: str,
        user_id: str,
        requester_id: str,
    ) -> bool:
        """Remove a member from a channel"""
        # Verify channel exists
        channel = ChannelService.get_channel(db, channel_id)
        if not channel:
            return False

        # Get member to remove
        member_query = select(ChannelMember).where(
            and_(
                ChannelMember.channel_id == UUID(channel_id),
                ChannelMember.user_id == user_id,
            )
        )
        member = db.execute(member_query).scalar_one_or_none()

        if not member:
            return False

        # Check permissions
        # - User can remove themselves
        # - Admins/owners can remove members
        # - Owners can remove anyone
        if user_id != requester_id:
            requester_query = select(ChannelMember).where(
                and_(
                    ChannelMember.channel_id == UUID(channel_id),
                    ChannelMember.user_id == requester_id,
                )
            )
            requester_member = db.execute(requester_query).scalar_one_or_none()

            if not requester_member:
                raise PermissionError("You are not a member of this channel")

            # Can't remove owner unless you're the owner
            if member.role == MemberRole.OWNER and requester_member.role != MemberRole.OWNER:
                raise PermissionError("Only owners can remove other owners")

            # Must be admin or owner to remove others
            if requester_member.role not in [MemberRole.OWNER, MemberRole.ADMIN]:
                raise PermissionError("Only admins or owners can remove members")

        # Remove member
        db.delete(member)
        db.commit()

        # Publish Kafka event
        await publish_channel_event(
            event_type=EventType.CHANNEL_MEMBER_REMOVED,
            channel_id=channel_id,
            workspace_id=str(channel.workspace_id),
            user_id=user_id,
            removed_by=requester_id,
        )

        logger.info(f"User {user_id} removed from channel {channel_id} by {requester_id}")
        return True


class DMService:
    """Service for direct message operations"""

    @staticmethod
    async def create_dm(
        db: Session,
        workspace_id: str,
        user_id: str,
        request: CreateDMRequest,
    ) -> DirectMessage:
        """Create or get existing DM session"""
        # For 1-on-1 DM, check if session already exists
        if len(request.participant_ids) == 1:
            other_user_id = request.participant_ids[0]

            # Find existing DM between these two users
            existing_dm_query = select(DirectMessage).join(DMParticipant).where(
                and_(
                    DirectMessage.workspace_id == UUID(workspace_id),
                    DMParticipant.user_id.in_([user_id, other_user_id])
                )
            ).group_by(DirectMessage.dm_id).having(
                func.count(DMParticipant.user_id) == 2
            )

            # Check if both users are in the same DM
            existing_dms = db.execute(existing_dm_query).scalars().all()
            for dm in existing_dms:
                participants = db.execute(
                    select(DMParticipant.user_id).where(DMParticipant.dm_id == dm.dm_id)
                ).scalars().all()

                if set(participants) == {user_id, other_user_id}:
                    logger.info(f"Returning existing DM {dm.dm_id} for users {user_id} and {other_user_id}")
                    return dm

        # Create new DM
        dm = DirectMessage(
            dm_id=uuid4(),
            workspace_id=UUID(workspace_id),
            created_at=datetime.utcnow(),
        )

        db.add(dm)
        db.flush()

        # Add participants
        for participant_id in [user_id] + request.participant_ids:
            if participant_id == user_id and user_id in request.participant_ids:
                # Don't duplicate if user already in list
                continue

            participant = DMParticipant(
                dm_id=dm.dm_id,
                user_id=participant_id,
                joined_at=datetime.utcnow(),
            )
            db.add(participant)

        db.commit()
        db.refresh(dm)

        # Publish Kafka event
        await publish_channel_event(
            event_type=EventType.DM_CREATED,
            channel_id=str(dm.dm_id),
            workspace_id=workspace_id,
            user_id=user_id,
        )

        logger.info(f"DM {dm.dm_id} created by user {user_id}")
        return dm

    @staticmethod
    def get_user_dms(
        db: Session,
        workspace_id: str,
        user_id: str,
    ) -> List[DirectMessage]:
        """Get all DM sessions for a user"""
        query = select(DirectMessage).join(DMParticipant).where(
            and_(
                DirectMessage.workspace_id == UUID(workspace_id),
                DMParticipant.user_id == user_id,
            )
        )
        query = query.order_by(DirectMessage.created_at.desc())
        return db.execute(query).scalars().all()

    @staticmethod
    def get_dm_participants(db: Session, dm_id: str) -> List[str]:
        """Get participant user IDs for a DM"""
        query = select(DMParticipant.user_id).where(DMParticipant.dm_id == UUID(dm_id))
        return db.execute(query).scalars().all()
