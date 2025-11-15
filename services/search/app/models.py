"""Pydantic models for Search Service"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MessageSearchResult(BaseModel):
    """Message search result"""
    message_id: str
    channel_id: Optional[str] = None
    dm_id: Optional[str] = None
    user_id: str
    username: str
    content: str
    content_snippet: Optional[str] = None  # Highlighted snippet
    created_at: datetime
    relevance_score: Optional[float] = None


class MessageSearchResponse(BaseModel):
    """Message search response"""
    results: List[MessageSearchResult]
    total: int
    limit: int
    offset: int


class FileSearchResult(BaseModel):
    """File search result"""
    file_id: str
    filename: str
    content_type: str
    size_bytes: int
    uploader_id: str
    channel_id: Optional[str] = None
    dm_id: Optional[str] = None
    created_at: datetime
    relevance_score: Optional[float] = None


class FileSearchResponse(BaseModel):
    """File search response"""
    results: List[FileSearchResult]
    total: int
    limit: int
    offset: int


class UnifiedSearchResponse(BaseModel):
    """Unified search response (messages + files)"""
    messages: List[MessageSearchResult]
    files: List[FileSearchResult]
    total_messages: int
    total_files: int


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    status_code: int
    details: Optional[dict] = None
