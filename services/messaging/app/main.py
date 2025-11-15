"""CoLink Messaging Service - Messages, threads, and reactions"""

import logging
import os
import sys
from typing import Optional
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
    Message,
    CreateMessageRequest,
    UpdateMessageRequest,
    MessagesResponse,
    ThreadMessage,
    CreateThreadReplyRequest,
    ThreadRepliesResponse,
    Reaction,
    AddReactionRequest,
    ReactionsResponse,
)
from .service import MessageService, ThreadService, ReactionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "colink")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://colink:colink@localhost:5432/colink")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


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
    logger.info("Starting Messaging Service...")

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
        # Continue without Kafka - it's not critical for basic functionality

    yield

    # Cleanup
    logger.info("Shutting down Messaging Service...")
    await close_kafka_producer()


app = FastAPI(
    title="CoLink Messaging Service API",
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
    return {"status": "healthy", "service": "messaging"}


@app.post("/channels/{channel_id}/messages", response_model=Message, status_code=201, tags=["Messages"])
async def send_message(
    channel_id: str,
    message: CreateMessageRequest,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Message:
    """Send a new message to a channel"""
    try:
        db_message = await MessageService.create_message(
            db=db,
            channel_id=channel_id,
            dm_id=None,
            user_id=user.user_id,
            request=message,
        )

        return Message(
            message_id=str(db_message.message_id),
            channel_id=str(db_message.channel_id) if db_message.channel_id else None,
            dm_id=None,
            user_id=db_message.user_id,
            username=user.username,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            content=db_message.content,
            mentions=message.mentions,
            attachments=message.attachments,
            created_at=db_message.created_at,
        )
    except Exception as e:
        logger.error(f"Error creating message: {e}")
        raise HTTPException(status_code=500, detail="Failed to create message")


@app.get("/channels/{channel_id}/messages", response_model=MessagesResponse, tags=["Messages"])
async def get_messages(
    channel_id: str,
    limit: int = Query(50, ge=1, le=100),
    before: Optional[str] = None,
    after: Optional[str] = None,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessagesResponse:
    """Get messages from a channel (paginated)"""
    try:
        db_messages, has_more = MessageService.get_messages(
            db=db,
            channel_id=channel_id,
            limit=limit,
            before=before,
            after=after,
        )

        messages = [
            Message(
                message_id=str(msg.message_id),
                channel_id=str(msg.channel_id) if msg.channel_id else None,
                dm_id=str(msg.dm_id) if msg.dm_id else None,
                user_id=msg.user_id,
                username="",  # TODO: Fetch from user service
                display_name=None,
                content=msg.content,
                created_at=msg.created_at,
                edited_at=msg.updated_at,
            )
            for msg in db_messages
        ]

        return MessagesResponse(
            messages=messages,
            has_more=has_more,
            before_cursor=str(messages[0].message_id) if messages else None,
            after_cursor=str(messages[-1].message_id) if messages else None,
        )
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch messages")


@app.get("/messages/{message_id}", response_model=Message, tags=["Messages"])
async def get_message(
    message_id: str,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Message:
    """Get a specific message by ID"""
    db_message = MessageService.get_message(db, message_id)
    if not db_message:
        raise HTTPException(status_code=404, detail="Message not found")

    return Message(
        message_id=str(db_message.message_id),
        channel_id=str(db_message.channel_id) if db_message.channel_id else None,
        dm_id=str(db_message.dm_id) if db_message.dm_id else None,
        user_id=db_message.user_id,
        username="",  # TODO: Fetch from user service
        display_name=None,
        content=db_message.content,
        created_at=db_message.created_at,
        edited_at=db_message.updated_at,
    )


@app.put("/messages/{message_id}", response_model=Message, tags=["Messages"])
async def update_message(
    message_id: str,
    update: UpdateMessageRequest,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Message:
    """Edit a message (author only)"""
    try:
        db_message = await MessageService.update_message(
            db=db,
            message_id=message_id,
            user_id=user.user_id,
            request=update,
        )

        if not db_message:
            raise HTTPException(status_code=404, detail="Message not found")

        return Message(
            message_id=str(db_message.message_id),
            channel_id=str(db_message.channel_id) if db_message.channel_id else None,
            dm_id=str(db_message.dm_id) if db_message.dm_id else None,
            user_id=db_message.user_id,
            username=user.username,
            display_name=user.display_name,
            content=db_message.content,
            created_at=db_message.created_at,
            edited_at=db_message.updated_at,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating message: {e}")
        raise HTTPException(status_code=500, detail="Failed to update message")


@app.delete("/messages/{message_id}", status_code=204, tags=["Messages"])
async def delete_message(
    message_id: str,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a message (soft delete)"""
    try:
        # TODO: Check if user is admin
        is_admin = False  # Placeholder - would need to check user roles

        success = await MessageService.delete_message(
            db=db,
            message_id=message_id,
            user_id=user.user_id,
            is_admin=is_admin,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Message not found")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete message")


@app.post("/messages/{message_id}/threads", response_model=ThreadMessage, status_code=201, tags=["Threads"])
async def create_thread_reply(
    message_id: str,
    reply: CreateThreadReplyRequest,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ThreadMessage:
    """Reply to a message in a thread"""
    try:
        db_thread_message = await ThreadService.create_thread_reply(
            db=db,
            message_id=message_id,
            user_id=user.user_id,
            request=reply,
        )

        if not db_thread_message:
            raise HTTPException(status_code=404, detail="Parent message not found")

        return ThreadMessage(
            thread_message_id=str(db_thread_message.reply_id),
            parent_message_id=message_id,
            user_id=db_thread_message.user_id,
            username=user.username,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            content=db_thread_message.content,
            created_at=db_thread_message.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating thread reply: {e}")
        raise HTTPException(status_code=500, detail="Failed to create thread reply")


@app.get("/messages/{message_id}/threads", response_model=ThreadRepliesResponse, tags=["Threads"])
async def get_thread_replies(
    message_id: str,
    limit: int = Query(50, ge=1, le=100),
    after: Optional[str] = None,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ThreadRepliesResponse:
    """Get all replies in a thread"""
    try:
        db_replies, total, has_more = ThreadService.get_thread_replies(
            db=db,
            message_id=message_id,
            limit=limit,
            after=after,
        )

        replies = [
            ThreadMessage(
                thread_message_id=str(reply.reply_id),
                parent_message_id=message_id,
                user_id=reply.user_id,
                username="",  # TODO: Fetch from user service
                display_name=None,
                content=reply.content,
                created_at=reply.created_at,
            )
            for reply in db_replies
        ]

        return ThreadRepliesResponse(
            replies=replies,
            total=total,
            has_more=has_more,
        )
    except Exception as e:
        logger.error(f"Error fetching thread replies: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch thread replies")


@app.post("/messages/{message_id}/reactions", response_model=Reaction, status_code=201, tags=["Reactions"])
async def add_reaction(
    message_id: str,
    reaction: AddReactionRequest,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Reaction:
    """Add emoji reaction to a message"""
    try:
        db_reaction = await ReactionService.add_reaction(
            db=db,
            message_id=message_id,
            user_id=user.user_id,
            request=reaction,
        )

        if not db_reaction:
            raise HTTPException(status_code=404, detail="Message not found")

        return Reaction(
            reaction_id=str(db_reaction.reaction_id),
            message_id=str(db_reaction.message_id),
            user_id=db_reaction.user_id,
            username=user.username,
            emoji=db_reaction.emoji,
            created_at=db_reaction.created_at,
        )
    except ValueError as e:
        # Duplicate reaction
        raise HTTPException(status_code=409, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding reaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to add reaction")


@app.get("/messages/{message_id}/reactions", response_model=ReactionsResponse, tags=["Reactions"])
async def get_reactions(
    message_id: str,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReactionsResponse:
    """Get all reactions for a message"""
    try:
        db_reactions = ReactionService.get_reactions(db, message_id)

        reactions = [
            Reaction(
                reaction_id=str(react.reaction_id),
                message_id=str(react.message_id),
                user_id=react.user_id,
                username="",  # TODO: Fetch from user service
                emoji=react.emoji,
                created_at=react.created_at,
            )
            for react in db_reactions
        ]

        return ReactionsResponse(reactions=reactions)
    except Exception as e:
        logger.error(f"Error fetching reactions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch reactions")


@app.delete("/reactions/{reaction_id}", status_code=204, tags=["Reactions"])
async def remove_reaction(
    reaction_id: str,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove own reaction"""
    try:
        success = await ReactionService.remove_reaction(
            db=db,
            reaction_id=reaction_id,
            user_id=user.user_id,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Reaction not found")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing reaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove reaction")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
