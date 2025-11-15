"""CoLink Admin Service - Administration and moderation"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorDatabase

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from common.auth import init_jwt_handler, get_current_user, UserContext
from common.database import (
    get_mongodb,
    init_mongodb,
    init_kafka_producer,
    close_kafka_producer,
)
from .models import (
    AdminUserView,
    UsersListResponse,
    SuspendUserRequest,
    DeleteMessageRequest,
    AuditLogEntry,
    AuditLogResponse,
)
from .service import AdminUserService, ModerationService, AuditService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "colink")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/colink")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


def get_db() -> AsyncIOMotorDatabase:
    """Get MongoDB database"""
    return get_mongodb()


async def require_admin(user: UserContext = Depends(get_current_user)) -> UserContext:
    """
    Require admin role for endpoint access

    Checks if user has 'admin' in realm_roles
    """
    # Check if user has admin role
    # In a real implementation, this would check Keycloak roles
    # For now, we'll check if the user has an 'is_admin' attribute
    # or if 'admin' is in their roles

    # Simplified admin check - in production, check JWT realm_roles
    if not getattr(user, 'is_admin', False):
        # TODO: Parse JWT and check realm_roles for 'admin'
        logger.warning(f"User {user.username} attempted admin action without admin role")
        raise HTTPException(
            status_code=403,
            detail="Admin role required for this operation"
        )

    return user


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Admin Service...")

    # Initialize JWT handler
    init_jwt_handler(KEYCLOAK_URL, KEYCLOAK_REALM)

    # Initialize MongoDB
    try:
        await init_mongodb(MONGODB_URL)
        logger.info("MongoDB initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}")
        raise

    # Initialize Kafka producer
    try:
        await init_kafka_producer(KAFKA_BOOTSTRAP_SERVERS)
        logger.info("Kafka producer initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Kafka producer: {e}")

    yield

    # Cleanup
    logger.info("Shutting down Admin Service...")
    await close_kafka_producer()


app = FastAPI(
    title="CoLink Admin Service API",
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
    return {"status": "healthy", "service": "admin"}


# User Management Endpoints

@app.get("/admin/users", response_model=UsersListResponse, tags=["Users"])
async def list_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    request: Request = None,
    admin: UserContext = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UsersListResponse:
    """List all users (admin only)"""
    try:
        # Get auth token from request
        token = None
        if request and request.headers.get("authorization"):
            token = request.headers.get("authorization").replace("Bearer ", "")

        users, total = await AdminUserService.list_users(
            limit=limit,
            offset=offset,
            search=search,
            token=token,
        )

        # Enrich with suspension status
        admin_users = []
        for user in users:
            suspension = await AdminUserService.get_user_suspension(db, user.get("user_id"))

            admin_users.append(
                AdminUserView(
                    user_id=user.get("user_id"),
                    username=user.get("username", ""),
                    email=user.get("email", ""),
                    is_suspended=suspension is not None,
                    suspend_until=suspension.get("suspend_until") if suspension else None,
                    suspend_reason=suspension.get("reason") if suspension else None,
                    created_at=user.get("created_at", datetime.utcnow()),
                    last_login=user.get("last_login"),
                )
            )

        return UsersListResponse(users=admin_users, total=total)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")


@app.post("/admin/users/{user_id}/suspend", tags=["Users"])
async def suspend_user(
    user_id: str,
    request: SuspendUserRequest,
    admin: UserContext = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Suspend a user (admin only)"""
    try:
        success = await AdminUserService.suspend_user(
            db=db,
            user_id=user_id,
            admin_id=admin.user_id,
            admin_username=admin.username,
            request=request,
        )

        if not success:
            raise HTTPException(status_code=404, detail="User not found")

        return {"status": "suspended", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suspending user: {e}")
        raise HTTPException(status_code=500, detail="Failed to suspend user")


@app.post("/admin/users/{user_id}/activate", tags=["Users"])
async def activate_user(
    user_id: str,
    admin: UserContext = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Activate (unsuspend) a user (admin only)"""
    try:
        success = await AdminUserService.activate_user(
            db=db,
            user_id=user_id,
            admin_id=admin.user_id,
            admin_username=admin.username,
        )

        if not success:
            raise HTTPException(status_code=404, detail="User not found or not suspended")

        return {"status": "activated", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate user")


# Moderation Endpoints

@app.delete("/admin/messages/{message_id}", status_code=204, tags=["Moderation"])
async def delete_message_moderation(
    message_id: str,
    request_body: DeleteMessageRequest,
    request: Request,
    admin: UserContext = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Delete a message (moderation action, admin only)"""
    try:
        # Get auth token from request
        token = None
        if request.headers.get("authorization"):
            token = request.headers.get("authorization").replace("Bearer ", "")

        success = await ModerationService.delete_message(
            db=db,
            message_id=message_id,
            admin_id=admin.user_id,
            admin_username=admin.username,
            request=request_body,
            token=token,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Message not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete message")


# Audit Log Endpoints

@app.get("/admin/audit-log", response_model=AuditLogResponse, tags=["Audit"])
async def get_audit_log(
    action_type: Optional[str] = None,
    actor_id: Optional[str] = None,
    from_date: Optional[datetime] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: UserContext = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AuditLogResponse:
    """Get audit log (admin only)"""
    try:
        logs, total = await AuditService.get_audit_log(
            db=db,
            action_type=action_type,
            actor_id=actor_id,
            from_date=from_date,
            limit=limit,
            offset=offset,
        )

        audit_entries = [
            AuditLogEntry(
                audit_id=log.get("audit_id"),
                action_type=log.get("action_type"),
                actor_id=log.get("actor_id"),
                actor_username=log.get("actor_username"),
                target_id=log.get("target_id"),
                target_type=log.get("target_type"),
                details=log.get("details", {}),
                timestamp=log.get("timestamp"),
            )
            for log in logs
        ]

        return AuditLogResponse(logs=audit_entries, total=total)
    except Exception as e:
        logger.error(f"Error getting audit log: {e}")
        raise HTTPException(status_code=500, detail="Failed to get audit log")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)
