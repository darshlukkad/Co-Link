"""
Admin Service business logic

Handles user management, content moderation, and audit logging.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase
import httpx

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from common.database import publish_event, EventType, KafkaTopic
from .models import SuspendUserRequest, DeleteMessageRequest

logger = logging.getLogger(__name__)

# Service URLs
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://localhost:8001")
MESSAGING_SERVICE_URL = os.getenv("MESSAGING_SERVICE_URL", "http://localhost:8002")


class AdminUserService:
    """Service for admin user management"""

    @staticmethod
    async def list_users(
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        token: str = None,
    ) -> Tuple[List[dict], int]:
        """
        List users by calling Users Service

        Returns:
            Tuple of (users, total_count)
        """
        async with httpx.AsyncClient() as client:
            params = {
                "limit": limit,
                "offset": offset,
            }
            if search:
                params["search"] = search

            headers = {"Authorization": f"Bearer {token}"} if token else {}

            try:
                response = await client.get(
                    f"{USERS_SERVICE_URL}/users",
                    params=params,
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

                users = data.get("users", [])
                total = data.get("total", len(users))

                return users, total
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch users: {e}")
                raise

    @staticmethod
    async def suspend_user(
        db: AsyncIOMotorDatabase,
        user_id: str,
        admin_id: str,
        admin_username: str,
        request: SuspendUserRequest,
    ) -> bool:
        """Suspend a user"""
        # Calculate suspension end time
        suspend_until = None
        if request.duration_hours:
            suspend_until = datetime.utcnow() + timedelta(hours=request.duration_hours)

        # Store suspension in MongoDB
        suspension_doc = {
            "_id": str(uuid4()),
            "user_id": user_id,
            "suspended_by": admin_id,
            "reason": request.reason,
            "suspended_at": datetime.utcnow(),
            "suspend_until": suspend_until,
            "is_active": True,
        }

        await db.user_suspensions.insert_one(suspension_doc)

        # Log audit event
        await AuditService.log_action(
            db=db,
            action_type="suspend_user",
            actor_id=admin_id,
            actor_username=admin_username,
            target_id=user_id,
            target_type="user",
            details={
                "reason": request.reason,
                "duration_hours": request.duration_hours,
                "suspend_until": suspend_until.isoformat() if suspend_until else None,
            },
        )

        # Publish Kafka event
        await publish_event(
            topic=KafkaTopic.USERS,
            event_type=EventType.USER_UPDATED,
            data={
                "user_id": user_id,
                "action": "suspended",
                "suspended_by": admin_id,
                "reason": request.reason,
                "suspend_until": suspend_until.isoformat() if suspend_until else None,
            },
            key=user_id,
        )

        logger.info(f"User {user_id} suspended by admin {admin_id}")
        return True

    @staticmethod
    async def activate_user(
        db: AsyncIOMotorDatabase,
        user_id: str,
        admin_id: str,
        admin_username: str,
    ) -> bool:
        """Activate (unsuspend) a user"""
        # Deactivate all active suspensions
        result = await db.user_suspensions.update_many(
            {"user_id": user_id, "is_active": True},
            {"$set": {"is_active": False, "unsuspended_at": datetime.utcnow()}}
        )

        if result.modified_count == 0:
            return False

        # Log audit event
        await AuditService.log_action(
            db=db,
            action_type="activate_user",
            actor_id=admin_id,
            actor_username=admin_username,
            target_id=user_id,
            target_type="user",
            details={"action": "unsuspended"},
        )

        # Publish Kafka event
        await publish_event(
            topic=KafkaTopic.USERS,
            event_type=EventType.USER_UPDATED,
            data={
                "user_id": user_id,
                "action": "activated",
                "activated_by": admin_id,
            },
            key=user_id,
        )

        logger.info(f"User {user_id} activated by admin {admin_id}")
        return True

    @staticmethod
    async def get_user_suspension(
        db: AsyncIOMotorDatabase,
        user_id: str,
    ) -> Optional[dict]:
        """Get active suspension for a user"""
        suspension = await db.user_suspensions.find_one(
            {
                "user_id": user_id,
                "is_active": True,
                "$or": [
                    {"suspend_until": {"$exists": False}},  # Permanent
                    {"suspend_until": None},  # Permanent
                    {"suspend_until": {"$gt": datetime.utcnow()}},  # Not expired
                ]
            }
        )
        return suspension


class ModerationService:
    """Service for content moderation"""

    @staticmethod
    async def delete_message(
        db: AsyncIOMotorDatabase,
        message_id: str,
        admin_id: str,
        admin_username: str,
        request: DeleteMessageRequest,
        token: str,
    ) -> bool:
        """Delete a message (moderation action)"""
        # Call messaging service to delete the message
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}

            try:
                response = await client.delete(
                    f"{MESSAGING_SERVICE_URL}/messages/{message_id}",
                    headers=headers,
                    timeout=10.0,
                )

                if response.status_code == 404:
                    return False

                response.raise_for_status()

            except httpx.HTTPError as e:
                logger.error(f"Failed to delete message: {e}")
                raise

        # Log audit event
        await AuditService.log_action(
            db=db,
            action_type="delete_message",
            actor_id=admin_id,
            actor_username=admin_username,
            target_id=message_id,
            target_type="message",
            details={
                "reason": request.reason,
                "moderation_action": True,
            },
        )

        # Publish moderation event
        await publish_event(
            topic=KafkaTopic.AUDIT,
            event_type=EventType.MESSAGE_DELETED,
            data={
                "message_id": message_id,
                "deleted_by": admin_id,
                "reason": request.reason,
                "moderation_action": True,
            },
            key=message_id,
        )

        logger.info(f"Message {message_id} deleted by admin {admin_id}")
        return True


class AuditService:
    """Service for audit logging"""

    @staticmethod
    async def log_action(
        db: AsyncIOMotorDatabase,
        action_type: str,
        actor_id: str,
        actor_username: str,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
        details: dict = None,
    ):
        """Log an admin action"""
        audit_entry = {
            "_id": str(uuid4()),
            "audit_id": str(uuid4()),
            "action_type": action_type,
            "actor_id": actor_id,
            "actor_username": actor_username,
            "target_id": target_id,
            "target_type": target_type,
            "details": details or {},
            "timestamp": datetime.utcnow(),
        }

        await db.admin_audit.insert_one(audit_entry)
        logger.info(f"Audit log: {action_type} by {actor_username} ({actor_id})")

    @staticmethod
    async def get_audit_log(
        db: AsyncIOMotorDatabase,
        action_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[dict], int]:
        """Get audit log with filters"""
        # Build query
        query = {}

        if action_type:
            query["action_type"] = action_type

        if actor_id:
            query["actor_id"] = actor_id

        if from_date:
            query["timestamp"] = {"$gte": from_date}

        # Get total count
        total = await db.admin_audit.count_documents(query)

        # Get logs
        cursor = db.admin_audit.find(query).sort("timestamp", -1).skip(offset).limit(limit)
        logs = await cursor.to_list(length=limit)

        return logs, total
