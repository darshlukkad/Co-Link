"""
CoLink Users Service

User profiles, status management, and user-related operations.
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Add parent directory to path for common modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from common.auth import (
    init_jwt_handler,
    get_current_user,
    UserContext,
)
from .models import (
    UserProfile,
    UpdateProfileRequest,
    UserStatus,
    SetStatusRequest,
    UserSearchResponse,
    HealthResponse,
    ErrorResponse,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Environment variables
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "colink")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "colink-api")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

# Prometheus metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    logger.info("Starting CoLink Users Service...")

    # Initialize JWT handler
    init_jwt_handler(
        keycloak_url=KEYCLOAK_URL,
        realm=KEYCLOAK_REALM,
        client_id=KEYCLOAK_CLIENT_ID,
    )
    logger.info("JWT handler initialized")

    yield

    logger.info("Shutting down CoLink Users Service...")


# Create FastAPI app
app = FastAPI(
    title="CoLink Users Service API",
    description="User profiles, status management, and user operations",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health endpoints
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check",
)
async def health_check():
    """Service health check"""
    return HealthResponse(status="healthy", service="users")


@app.get(
    "/ready",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Readiness check",
)
async def readiness_check():
    """Service readiness check"""
    # TODO: Check database connectivity
    return HealthResponse(status="ready", service="users")


@app.get("/metrics", tags=["Health"])
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Profile endpoints
@app.get(
    "/users/me",
    response_model=UserProfile,
    tags=["Profile"],
    summary="Get current user profile",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_current_user_profile(
    user: UserContext = Depends(get_current_user),
) -> UserProfile:
    """
    Get the profile of the currently authenticated user.

    Returns user profile with email, display name, avatar, etc.
    """
    # TODO: Fetch from database
    # For now, return mock data based on JWT claims
    return UserProfile(
        user_id=user.user_id,
        username=user.username,
        email=user.email or f"{user.username}@example.com",
        display_name=user.display_name,
        avatar_url=None,
        bio=None,
        timezone="America/New_York",
        created_at=datetime.utcnow(),
        updated_at=None,
    )


@app.put(
    "/users/me",
    response_model=UserProfile,
    tags=["Profile"],
    summary="Update current user profile",
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def update_current_user_profile(
    profile_update: UpdateProfileRequest,
    user: UserContext = Depends(get_current_user),
) -> UserProfile:
    """
    Update the profile of the currently authenticated user.

    Can update: display_name, avatar_url, bio, timezone
    """
    # TODO: Update in database
    logger.info(f"Updating profile for user {user.user_id}: {profile_update}")

    return UserProfile(
        user_id=user.user_id,
        username=user.username,
        email=user.email or f"{user.username}@example.com",
        display_name=profile_update.display_name or user.display_name,
        avatar_url=profile_update.avatar_url,
        bio=profile_update.bio,
        timezone=profile_update.timezone or "America/New_York",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@app.get(
    "/users/{user_id}",
    response_model=UserProfile,
    tags=["Profile"],
    summary="Get user by ID",
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse},
    },
)
async def get_user_by_id(
    user_id: str,
    _current_user: UserContext = Depends(get_current_user),
) -> UserProfile:
    """
    Get another user's public profile.

    Returns public profile information (no private data).
    """
    # TODO: Fetch from database
    if user_id == _current_user.user_id:
        return await get_current_user_profile(_current_user)

    # Mock data for other users
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"User {user_id} not found",
    )


# Status endpoints
@app.post(
    "/users/me/status",
    response_model=UserStatus,
    tags=["Status"],
    summary="Set user status",
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def set_user_status(
    status_request: SetStatusRequest,
    user: UserContext = Depends(get_current_user),
) -> UserStatus:
    """
    Set custom status text and emoji.

    Status can optionally expire after a specified number of minutes.
    """
    # Calculate expiry
    expiry = None
    if status_request.expiry_minutes:
        expiry = datetime.utcnow() + timedelta(minutes=status_request.expiry_minutes)

    # TODO: Store in database (user_status table)
    logger.info(f"Setting status for user {user.user_id}: {status_request}")

    return UserStatus(
        user_id=user.user_id,
        status_text=status_request.status_text,
        status_emoji=status_request.status_emoji,
        status_expiry=expiry,
        updated_at=datetime.utcnow(),
    )


@app.delete(
    "/users/me/status",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Status"],
    summary="Clear user status",
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def clear_user_status(
    user: UserContext = Depends(get_current_user),
):
    """
    Remove custom status.

    Clears both status text and emoji.
    """
    # TODO: Clear in database
    logger.info(f"Clearing status for user {user.user_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Search endpoints
@app.get(
    "/users/search",
    response_model=UserSearchResponse,
    tags=["Search"],
    summary="Search users",
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def search_users(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    _current_user: UserContext = Depends(get_current_user),
) -> UserSearchResponse:
    """
    Search for users by name or email.

    Returns paginated list of matching users.
    """
    # TODO: Search in database
    logger.info(f"Searching users: q={q}, limit={limit}, offset={offset}")

    # Mock empty results
    return UserSearchResponse(
        users=[],
        total=0,
        limit=limit,
        offset=offset,
    )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return ErrorResponse(
        error=exc.detail,
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    logger.exception(f"Unexpected error: {exc}")
    return ErrorResponse(
        error="Internal server error",
        status_code=500,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )
