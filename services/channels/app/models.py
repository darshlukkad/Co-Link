"""Pydantic models for Channels Service"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class Channel(BaseModel):
    """Channel response model"""
    channel_id: str
    workspace_id: str
    name: str
    description: Optional[str] = None
    is_private: bool = False
    is_archived: bool = False
    member_count: Optional[int] = 0
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class CreateChannelRequest(BaseModel):
    """Create channel request"""
    name: str = Field(..., min_length=1, max_length=80)
    description: Optional[str] = Field(None, max_length=250)
    is_private: bool = False


class UpdateChannelRequest(BaseModel):
    """Update channel request"""
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    description: Optional[str] = Field(None, max_length=250)


class ChannelsResponse(BaseModel):
    """List channels response"""
    channels: List[Channel]
    total: int


class Member(BaseModel):
    """Channel member response model"""
    user_id: str
    channel_id: str
    role: str  # owner, admin, member
    joined_at: datetime


class AddMemberRequest(BaseModel):
    """Add member request"""
    user_id: str
    role: str = Field(default="member", pattern="^(member|admin)$")


class MembersResponse(BaseModel):
    """List members response"""
    members: List[Member]


class DirectMessage(BaseModel):
    """DM session response model"""
    dm_id: str
    workspace_id: str
    participants: List[str]  # List of user IDs
    created_at: datetime


class CreateDMRequest(BaseModel):
    """Create DM request"""
    participant_ids: List[str] = Field(..., min_length=1, max_length=1)


class DMsResponse(BaseModel):
    """List DMs response"""
    dms: List[DirectMessage]


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    status_code: int
    details: Optional[dict] = None
