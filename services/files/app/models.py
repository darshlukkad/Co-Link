"""Pydantic models for Files Service"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class VirusScanStatus(str, Enum):
    """Virus scan status"""
    PENDING = "pending"
    CLEAN = "clean"
    INFECTED = "infected"


class UploadUrlRequest(BaseModel):
    """Request for presigned upload URL"""
    filename: str = Field(..., max_length=255)
    content_type: str
    size_bytes: int = Field(..., le=104857600)  # 100MB max
    channel_id: Optional[str] = None
    dm_id: Optional[str] = None


class UploadUrlResponse(BaseModel):
    """Presigned upload URL response"""
    file_id: str
    upload_url: str
    expires_at: datetime


class DownloadUrlResponse(BaseModel):
    """Presigned download URL response"""
    download_url: str
    expires_at: datetime


class FileMetadata(BaseModel):
    """File metadata response"""
    file_id: str
    workspace_id: str
    channel_id: Optional[str] = None
    dm_id: Optional[str] = None
    uploader_id: str
    filename: str
    content_type: str
    size_bytes: int
    virus_scan_status: VirusScanStatus = VirusScanStatus.PENDING
    s3_bucket: Optional[str] = None
    s3_key: Optional[str] = None
    created_at: datetime
    uploaded_at: Optional[datetime] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    status_code: int
    details: Optional[dict] = None
