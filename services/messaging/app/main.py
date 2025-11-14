"""CoLink Messaging Service - Messages, threads, and reactions"""

import logging
import os
import sys
import uuid
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from common.auth import init_jwt_handler, get_current_user, UserContext
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "colink")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Messaging Service...")
    init_jwt_handler(KEYCLOAK_URL, KEYCLOAK_REALM)
    yield
    logger.info("Shutting down Messaging Service...")


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
) -> Message:
    """Send a new message to a channel"""
    # TODO: Store in database, publish to Kafka
    logger.info(f"User {user.username} sending message to channel {channel_id}")

    return Message(
        message_id=str(uuid.uuid4()),
        channel_id=channel_id,
        user_id=user.user_id,
        username=user.username,
        display_name=user.display_name,
        content=message.content,
        mentions=message.mentions,
        attachments=message.attachments,
        created_at=datetime.utcnow(),
    )


@app.get("/channels/{channel_id}/messages", response_model=MessagesResponse, tags=["Messages"])
async def get_messages(
    channel_id: str,
    limit: int = Query(50, ge=1, le=100),
    before: Optional[str] = None,
    after: Optional[str] = None,
    user: UserContext = Depends(get_current_user),
) -> MessagesResponse:
    """Get messages from a channel (paginated)"""
    # TODO: Fetch from database
    logger.info(f"Fetching messages for channel {channel_id}")

    return MessagesResponse(
        messages=[],
        has_more=False,
    )


@app.get("/messages/{message_id}", response_model=Message, tags=["Messages"])
async def get_message(
    message_id: str,
    user: UserContext = Depends(get_current_user),
) -> Message:
    """Get a specific message by ID"""
    raise HTTPException(status_code=404, detail="Message not found")


@app.put("/messages/{message_id}", response_model=Message, tags=["Messages"])
async def update_message(
    message_id: str,
    update: UpdateMessageRequest,
    user: UserContext = Depends(get_current_user),
) -> Message:
    """Edit a message (author only)"""
    # TODO: Verify ownership, update in DB
    raise HTTPException(status_code=404, detail="Message not found")


@app.delete("/messages/{message_id}", status_code=204, tags=["Messages"])
async def delete_message(
    message_id: str,
    user: UserContext = Depends(get_current_user),
):
    """Delete a message (soft delete)"""
    # TODO: Verify ownership or admin, soft delete
    logger.info(f"Deleting message {message_id}")


@app.post("/messages/{message_id}/threads", response_model=ThreadMessage, status_code=201, tags=["Threads"])
async def create_thread_reply(
    message_id: str,
    reply: CreateThreadReplyRequest,
    user: UserContext = Depends(get_current_user),
) -> ThreadMessage:
    """Reply to a message in a thread"""
    # TODO: Store in DB
    return ThreadMessage(
        thread_message_id=str(uuid.uuid4()),
        parent_message_id=message_id,
        user_id=user.user_id,
        username=user.username,
        display_name=user.display_name,
        content=reply.content,
        created_at=datetime.utcnow(),
    )


@app.get("/messages/{message_id}/threads", response_model=ThreadRepliesResponse, tags=["Threads"])
async def get_thread_replies(
    message_id: str,
    limit: int = Query(50, ge=1, le=100),
    user: UserContext = Depends(get_current_user),
) -> ThreadRepliesResponse:
    """Get all replies in a thread"""
    return ThreadRepliesResponse(replies=[], total=0, has_more=False)


@app.post("/messages/{message_id}/reactions", response_model=Reaction, status_code=201, tags=["Reactions"])
async def add_reaction(
    message_id: str,
    reaction: AddReactionRequest,
    user: UserContext = Depends(get_current_user),
) -> Reaction:
    """Add emoji reaction to a message"""
    # TODO: Check for duplicate, store in DB
    return Reaction(
        reaction_id=str(uuid.uuid4()),
        message_id=message_id,
        user_id=user.user_id,
        username=user.username,
        emoji=reaction.emoji,
        created_at=datetime.utcnow(),
    )


@app.get("/messages/{message_id}/reactions", response_model=ReactionsResponse, tags=["Reactions"])
async def get_reactions(
    message_id: str,
    user: UserContext = Depends(get_current_user),
) -> ReactionsResponse:
    """Get all reactions for a message"""
    return ReactionsResponse(reactions=[])


@app.delete("/reactions/{reaction_id}", status_code=204, tags=["Reactions"])
async def remove_reaction(
    reaction_id: str,
    user: UserContext = Depends(get_current_user),
):
    """Remove own reaction"""
    logger.info(f"Removing reaction {reaction_id}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
