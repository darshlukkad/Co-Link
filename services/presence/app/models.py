"""
WebSocket message models for Presence Service
"""

from datetime import datetime
from typing import Optional, Literal, Any
from pydantic import BaseModel, Field


# Message types
MessageType = Literal[
    "subscribe",
    "unsubscribe",
    "typing",
    "ping",
    "pong",
    "subscribed",
    "unsubscribed",
    "message",
    "presence",
    "error",
]

# Presence statuses
PresenceStatus = Literal["online", "away", "offline"]


class WSMessage(BaseModel):
    """Base WebSocket message"""

    type: MessageType
    data: Optional[dict] = None


class SubscribeMessage(BaseModel):
    """Subscribe to a channel or DM"""

    type: Literal["subscribe"]
    channel_id: Optional[str] = None
    dm_id: Optional[str] = None


class UnsubscribeMessage(BaseModel):
    """Unsubscribe from a channel or DM"""

    type: Literal["unsubscribe"]
    channel_id: Optional[str] = None
    dm_id: Optional[str] = None


class TypingMessage(BaseModel):
    """Typing indicator"""

    type: Literal["typing"]
    channel_id: Optional[str] = None
    dm_id: Optional[str] = None


class PingMessage(BaseModel):
    """Ping for heartbeat"""

    type: Literal["ping"]


# Server → Client messages


class SubscribedMessage(BaseModel):
    """Confirmation of subscription"""

    type: Literal["subscribed"] = "subscribed"
    channel_id: Optional[str] = None
    dm_id: Optional[str] = None


class UnsubscribedMessage(BaseModel):
    """Confirmation of unsubscription"""

    type: Literal["unsubscribed"] = "unsubscribed"
    channel_id: Optional[str] = None
    dm_id: Optional[str] = None


class MessageBroadcast(BaseModel):
    """Broadcast message to subscribers"""

    type: Literal["message"] = "message"
    data: dict


class PresenceBroadcast(BaseModel):
    """User presence update"""

    type: Literal["presence"] = "presence"
    user_id: str
    username: str
    status: PresenceStatus
    timestamp: datetime


class TypingBroadcast(BaseModel):
    """Typing indicator broadcast"""

    type: Literal["typing"] = "typing"
    channel_id: Optional[str] = None
    dm_id: Optional[str] = None
    user_id: str
    username: str


class PongMessage(BaseModel):
    """Pong response to ping"""

    type: Literal["pong"] = "pong"
    timestamp: datetime


class ErrorMessage(BaseModel):
    """Error response"""

    type: Literal["error"] = "error"
    error: str
    code: Optional[int] = None


# Presence data structures


class UserPresence(BaseModel):
    """User presence information stored in Redis"""

    user_id: str
    username: str
    status: PresenceStatus
    connection_id: str
    last_seen: datetime


class ConnectionInfo(BaseModel):
    """WebSocket connection information"""

    connection_id: str
    user_id: str
    username: str
    connected_at: datetime
    last_heartbeat: datetime
    subscriptions: list[str] = Field(default_factory=list)  # channel/dm IDs
