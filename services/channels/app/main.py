"""CoLink Channels Service - Channel and DM management"""

import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from common.auth import init_jwt_handler, get_current_user, UserContext
from common.database import (
    get_postgres_engine,
    init_postgres,
    init_kafka_producer,
    close_kafka_producer,
)
from .database import Base
from .models import (
    Channel,
    CreateChannelRequest,
    UpdateChannelRequest,
    ChannelsResponse,
    Member,
    AddMemberRequest,
    MembersResponse,
    DirectMessage,
    CreateDMRequest,
    DMsResponse,
)
from .service import ChannelService, MemberService, DMService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "colink")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://colink:colink@localhost:5432/colink")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Default workspace ID (in a real app, this would come from auth context)
DEFAULT_WORKSPACE_ID = os.getenv("DEFAULT_WORKSPACE_ID", "00000000-0000-0000-0000-000000000001")


def get_db() -> Session:
    """Database session dependency"""
    engine = get_postgres_engine()
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Channels Service...")

    # Initialize JWT handler
    init_jwt_handler(KEYCLOAK_URL, KEYCLOAK_REALM)

    # Initialize database
    try:
        await init_postgres(POSTGRES_URL)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Initialize Kafka producer
    try:
        await init_kafka_producer(KAFKA_BOOTSTRAP_SERVERS)
        logger.info("Kafka producer initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Kafka producer: {e}")

    yield

    # Cleanup
    logger.info("Shutting down Channels Service...")
    await close_kafka_producer()


app = FastAPI(
    title="CoLink Channels Service API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "channels"}


# Channel endpoints

@app.post("/channels", response_model=Channel, status_code=201, tags=["Channels"])
async def create_channel(
    request: CreateChannelRequest,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Channel:
    """Create a new channel"""
    try:
        db_channel = await ChannelService.create_channel(
            db=db,
            workspace_id=DEFAULT_WORKSPACE_ID,
            user_id=user.user_id,
            request=request,
        )

        member_count = ChannelService.get_member_count(db, str(db_channel.channel_id))

        return Channel(
            channel_id=str(db_channel.channel_id),
            workspace_id=str(db_channel.workspace_id),
            name=db_channel.name,
            description=db_channel.description,
            is_private=db_channel.is_private,
            is_archived=db_channel.is_archived,
            member_count=member_count,
            created_by=db_channel.created_by,
            created_at=db_channel.created_at,
            updated_at=db_channel.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating channel: {e}")
        raise HTTPException(status_code=500, detail="Failed to create channel")


@app.get("/channels", response_model=ChannelsResponse, tags=["Channels"])
async def list_channels(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChannelsResponse:
    """List channels in workspace"""
    try:
        db_channels, total = ChannelService.get_channels(
            db=db,
            workspace_id=DEFAULT_WORKSPACE_ID,
            user_id=user.user_id,
            limit=limit,
            offset=offset,
        )

        channels = []
        for db_channel in db_channels:
            member_count = ChannelService.get_member_count(db, str(db_channel.channel_id))
            channels.append(
                Channel(
                    channel_id=str(db_channel.channel_id),
                    workspace_id=str(db_channel.workspace_id),
                    name=db_channel.name,
                    description=db_channel.description,
                    is_private=db_channel.is_private,
                    is_archived=db_channel.is_archived,
                    member_count=member_count,
                    created_by=db_channel.created_by,
                    created_at=db_channel.created_at,
                    updated_at=db_channel.updated_at,
                )
            )

        return ChannelsResponse(channels=channels, total=total)
    except Exception as e:
        logger.error(f"Error listing channels: {e}")
        raise HTTPException(status_code=500, detail="Failed to list channels")


@app.get("/channels/{channel_id}", response_model=Channel, tags=["Channels"])
async def get_channel(
    channel_id: str,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Channel:
    """Get channel details"""
    try:
        db_channel = ChannelService.get_channel(db, channel_id, user.user_id)
        if not db_channel:
            raise HTTPException(status_code=404, detail="Channel not found")

        member_count = ChannelService.get_member_count(db, channel_id)

        return Channel(
            channel_id=str(db_channel.channel_id),
            workspace_id=str(db_channel.workspace_id),
            name=db_channel.name,
            description=db_channel.description,
            is_private=db_channel.is_private,
            is_archived=db_channel.is_archived,
            member_count=member_count,
            created_by=db_channel.created_by,
            created_at=db_channel.created_at,
            updated_at=db_channel.updated_at,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting channel: {e}")
        raise HTTPException(status_code=500, detail="Failed to get channel")


@app.put("/channels/{channel_id}", response_model=Channel, tags=["Channels"])
async def update_channel(
    channel_id: str,
    request: UpdateChannelRequest,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Channel:
    """Update channel (owner/admin only)"""
    try:
        db_channel = await ChannelService.update_channel(
            db=db,
            channel_id=channel_id,
            user_id=user.user_id,
            request=request,
        )

        if not db_channel:
            raise HTTPException(status_code=404, detail="Channel not found")

        member_count = ChannelService.get_member_count(db, channel_id)

        return Channel(
            channel_id=str(db_channel.channel_id),
            workspace_id=str(db_channel.workspace_id),
            name=db_channel.name,
            description=db_channel.description,
            is_private=db_channel.is_private,
            is_archived=db_channel.is_archived,
            member_count=member_count,
            created_by=db_channel.created_by,
            created_at=db_channel.created_at,
            updated_at=db_channel.updated_at,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating channel: {e}")
        raise HTTPException(status_code=500, detail="Failed to update channel")


@app.delete("/channels/{channel_id}", status_code=204, tags=["Channels"])
async def archive_channel(
    channel_id: str,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Archive channel (owner only)"""
    try:
        success = await ChannelService.archive_channel(
            db=db,
            channel_id=channel_id,
            user_id=user.user_id,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Channel not found")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving channel: {e}")
        raise HTTPException(status_code=500, detail="Failed to archive channel")


# Member endpoints

@app.post("/channels/{channel_id}/members", response_model=Member, tags=["Members"])
async def add_member(
    channel_id: str,
    request: AddMemberRequest,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Member:
    """Add member to channel"""
    try:
        db_member = await MemberService.add_member(
            db=db,
            channel_id=channel_id,
            requester_id=user.user_id,
            request=request,
        )

        if not db_member:
            raise HTTPException(status_code=404, detail="Channel not found")

        return Member(
            user_id=db_member.user_id,
            channel_id=str(db_member.channel_id),
            role=db_member.role.value,
            joined_at=db_member.joined_at,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding member: {e}")
        raise HTTPException(status_code=500, detail="Failed to add member")


@app.get("/channels/{channel_id}/members", response_model=MembersResponse, tags=["Members"])
async def list_members(
    channel_id: str,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MembersResponse:
    """List channel members"""
    try:
        # Verify channel exists and user has access
        channel = ChannelService.get_channel(db, channel_id, user.user_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")

        db_members = MemberService.get_members(db, channel_id)

        members = [
            Member(
                user_id=m.user_id,
                channel_id=str(m.channel_id),
                role=m.role.value,
                joined_at=m.joined_at,
            )
            for m in db_members
        ]

        return MembersResponse(members=members)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing members: {e}")
        raise HTTPException(status_code=500, detail="Failed to list members")


@app.delete("/channels/{channel_id}/members/{user_id}", status_code=204, tags=["Members"])
async def remove_member(
    channel_id: str,
    user_id: str,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove member from channel"""
    try:
        success = await MemberService.remove_member(
            db=db,
            channel_id=channel_id,
            user_id=user_id,
            requester_id=user.user_id,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Member not found")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing member: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove member")


# DM endpoints

@app.post("/dms", response_model=DirectMessage, status_code=201, tags=["DMs"])
async def create_dm(
    request: CreateDMRequest,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DirectMessage:
    """Create or get DM session"""
    try:
        db_dm = await DMService.create_dm(
            db=db,
            workspace_id=DEFAULT_WORKSPACE_ID,
            user_id=user.user_id,
            request=request,
        )

        participants = DMService.get_dm_participants(db, str(db_dm.dm_id))

        return DirectMessage(
            dm_id=str(db_dm.dm_id),
            workspace_id=str(db_dm.workspace_id),
            participants=participants,
            created_at=db_dm.created_at,
        )
    except Exception as e:
        logger.error(f"Error creating DM: {e}")
        raise HTTPException(status_code=500, detail="Failed to create DM")


@app.get("/dms", response_model=DMsResponse, tags=["DMs"])
async def list_dms(
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DMsResponse:
    """List user's DM sessions"""
    try:
        db_dms = DMService.get_user_dms(
            db=db,
            workspace_id=DEFAULT_WORKSPACE_ID,
            user_id=user.user_id,
        )

        dms = []
        for db_dm in db_dms:
            participants = DMService.get_dm_participants(db, str(db_dm.dm_id))
            dms.append(
                DirectMessage(
                    dm_id=str(db_dm.dm_id),
                    workspace_id=str(db_dm.workspace_id),
                    participants=participants,
                    created_at=db_dm.created_at,
                )
            )

        return DMsResponse(dms=dms)
    except Exception as e:
        logger.error(f"Error listing DMs: {e}")
        raise HTTPException(status_code=500, detail="Failed to list DMs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8006, reload=True)
