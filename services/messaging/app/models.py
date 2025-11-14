"""Pydantic models for Messaging Service"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    message_id: str
    channel_id: Optional[str] = None
    dm_id: Optional[str] = None
    user_id: str
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    content: str = Field(..., max_length=4000)
    mentions: list[str] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)
    thread_id: Optional[str] = None
    thread_reply_count: Optional[int] = None
    reactions_summary: list[dict] = Field(default_factory=list)
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime


class CreateMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    mentions: list[str] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)


class UpdateMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class MessagesResponse(BaseModel):
    messages: list[Message]
    has_more: bool
    before_cursor: Optional[str] = None
    after_cursor: Optional[str] = None


class ThreadMessage(BaseModel):
    thread_message_id: str
    parent_message_id: str
    user_id: str
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    content: str = Field(..., max_length=4000)
    reactions_summary: list[dict] = Field(default_factory=list)
    created_at: datetime


class CreateThreadReplyRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class ThreadRepliesResponse(BaseModel):
    replies: list[ThreadMessage]
    total: int
    has_more: bool


class Reaction(BaseModel):
    reaction_id: str
    message_id: str
    user_id: str
    username: str
    emoji: str = Field(..., max_length=10)
    created_at: datetime


class AddReactionRequest(BaseModel):
    emoji: str = Field(..., min_length=1, max_length=10)


class ReactionsResponse(BaseModel):
    reactions: list[Reaction]


class ErrorResponse(BaseModel):
    error: str
    status_code: int
    details: Optional[dict] = None
