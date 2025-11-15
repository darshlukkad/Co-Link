"""Pydantic models for Admin Service"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AdminUserView(BaseModel):
    """Admin view of user"""
    user_id: str
    username: str
    email: str
    is_suspended: bool = False
    suspend_until: Optional[datetime] = None
    suspend_reason: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None


class UsersListResponse(BaseModel):
    """Users list response"""
    users: List[AdminUserView]
    total: int


class SuspendUserRequest(BaseModel):
    """Suspend user request"""
    reason: str
    duration_hours: Optional[int] = None  # None = permanent


class DeleteMessageRequest(BaseModel):
    """Delete message moderation request"""
    reason: str


class AuditLogEntry(BaseModel):
    """Audit log entry"""
    audit_id: str
    action_type: str
    actor_id: str
    actor_username: str
    target_id: Optional[str] = None
    target_type: Optional[str] = None  # user, message, channel
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class AuditLogResponse(BaseModel):
    """Audit log response"""
    logs: List[AuditLogEntry]
    total: int


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    status_code: int
    details: Optional[dict] = None
