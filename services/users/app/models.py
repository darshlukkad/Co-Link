"""
Pydantic models for Users Service

These models match the OpenAPI specification.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator


class UserProfile(BaseModel):
    """User profile response"""

    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    display_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = Field(None, example="America/New_York")
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "8c3f4d5e-1234-5678-90ab-cdef12345678",
                "username": "alice",
                "email": "alice@example.com",
                "display_name": "Alice Smith",
                "avatar_url": "https://example.com/avatars/alice.jpg",
                "bio": "Product Manager at CoLink",
                "timezone": "America/New_York",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T14:45:00Z",
            }
        }
    }


class UpdateProfileRequest(BaseModel):
    """Update user profile request"""

    display_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = Field(None, example="America/New_York")


class UserStatus(BaseModel):
    """User status (custom status with emoji)"""

    user_id: str
    status_text: Optional[str] = Field(None, max_length=100)
    status_emoji: Optional[str] = Field(None, max_length=10)
    status_expiry: Optional[datetime] = None
    updated_at: datetime


class SetStatusRequest(BaseModel):
    """Set user status request"""

    status_text: Optional[str] = Field(None, max_length=100)
    status_emoji: Optional[str] = Field(None, max_length=10)
    expiry_minutes: Optional[int] = Field(None, ge=1, le=1440)

    model_config = {
        "json_schema_extra": {
            "example": {
                "status_text": "In a meeting",
                "status_emoji": "📅",
                "expiry_minutes": 60,
            }
        }
    }


class UserSearchResponse(BaseModel):
    """User search results"""

    users: list[UserProfile]
    total: int
    limit: int
    offset: int


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = "healthy"
    service: str = "users"


class ErrorResponse(BaseModel):
    """Error response"""

    error: str
    status_code: int
    details: Optional[dict] = None
