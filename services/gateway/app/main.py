"""
CoLink API Gateway

Central entry point for all API requests.
Handles routing, authentication, rate limiting, and request aggregation.
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import sys

# Add parent directory to path to import common modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from common.auth import (
    init_jwt_handler,
    get_current_user,
    get_current_user_optional,
    require_admin,
    UserContext,
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
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Prometheus metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting CoLink API Gateway...")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Keycloak URL: {KEYCLOAK_URL}")
    logger.info(f"Keycloak Realm: {KEYCLOAK_REALM}")

    # Initialize JWT handler
    init_jwt_handler(
        keycloak_url=KEYCLOAK_URL,
        realm=KEYCLOAK_REALM,
        client_id=KEYCLOAK_CLIENT_ID,
    )
    logger.info("JWT handler initialized")

    yield

    # Shutdown
    logger.info("Shutting down CoLink API Gateway...")


# Create FastAPI app
app = FastAPI(
    title="CoLink API Gateway",
    description="Central API gateway for CoLink enterprise chat application",
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


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "gateway"}


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check endpoint"""
    # TODO: Check connectivity to Keycloak and other dependencies
    return {"status": "ready", "service": "gateway"}


@app.get("/metrics", tags=["Observability"])
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Authentication endpoints
@app.get("/auth/me", tags=["Authentication"])
async def get_current_user_info(user: UserContext = Depends(get_current_user)):
    """
    Get current authenticated user information

    Requires valid JWT token in Authorization header.
    """
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
        "roles": user.roles,
        "is_admin": user.is_admin,
        "email_verified": user.email_verified,
    }


@app.get("/auth/check", tags=["Authentication"])
async def check_authentication(user: UserContext = Depends(get_current_user_optional)):
    """
    Check if request is authenticated (optional)

    Returns user info if authenticated, otherwise returns guest status.
    """
    if user:
        return {
            "authenticated": True,
            "user_id": user.user_id,
            "username": user.username,
        }
    return {"authenticated": False}


# Admin-only endpoint example
@app.get("/admin/stats", tags=["Admin"])
async def admin_stats(user: UserContext = Depends(require_admin)):
    """
    Get admin statistics

    Requires 'admin' role.
    """
    return {
        "message": "Admin stats endpoint",
        "admin_user": user.username,
        "stats": {
            "total_users": 0,  # TODO: Implement
            "total_channels": 0,
            "total_messages": 0,
        },
    }


# Proxy endpoints (to be implemented)
@app.api_route(
    "/api/v1/{service}/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    tags=["Proxy"],
)
async def proxy_to_service(
    service: str,
    path: str,
    user: UserContext = Depends(get_current_user),
):
    """
    Proxy requests to backend services

    Routes:
    - /api/v1/users/* -> Users Service
    - /api/v1/channels/* -> Channels Service
    - /api/v1/messages/* -> Messaging Service
    - /api/v1/files/* -> Files Service
    - /api/v1/search/* -> Search Service
    - /api/v1/admin/* -> Admin Service
    """
    # TODO: Implement actual proxying to backend services
    return {
        "message": "Proxy endpoint (not yet implemented)",
        "service": service,
        "path": path,
        "user_id": user.user_id,
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    logger.exception(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
        },
    )


# Root endpoint
@app.get("/", tags=["General"])
async def root():
    """API Gateway root endpoint"""
    return {
        "service": "CoLink API Gateway",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
