"""
Files Service business logic

Handles file metadata storage in MongoDB and S3 operations.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from common.database import publish_event, EventType, KafkaTopic
from .models import UploadUrlRequest, VirusScanStatus
from .storage import (
    generate_s3_key,
    generate_presigned_upload_url,
    generate_presigned_download_url,
    verify_file_uploaded,
    delete_file_from_s3,
    S3_BUCKET,
)

logger = logging.getLogger(__name__)


class FileService:
    """Service for file operations"""

    @staticmethod
    async def create_upload_url(
        db: AsyncIOMotorDatabase,
        workspace_id: str,
        user_id: str,
        request: UploadUrlRequest,
    ) -> tuple[str, str, datetime]:
        """
        Create file metadata and generate presigned upload URL

        Returns:
            Tuple of (file_id, upload_url, expires_at)
        """
        # Generate file ID and S3 key
        file_id = str(uuid4())
        s3_key = generate_s3_key(workspace_id, file_id, request.filename)

        # Generate presigned URL
        upload_url, expires_at = generate_presigned_upload_url(
            s3_key=s3_key,
            content_type=request.content_type,
            size_bytes=request.size_bytes,
        )

        # Store metadata in MongoDB
        file_metadata = {
            "_id": file_id,
            "file_id": file_id,
            "workspace_id": workspace_id,
            "channel_id": request.channel_id,
            "dm_id": request.dm_id,
            "uploader_id": user_id,
            "filename": request.filename,
            "content_type": request.content_type,
            "size_bytes": request.size_bytes,
            "s3_bucket": S3_BUCKET,
            "s3_key": s3_key,
            "virus_scan_status": VirusScanStatus.PENDING.value,
            "created_at": datetime.utcnow(),
            "uploaded_at": None,
        }

        await db.files.insert_one(file_metadata)

        logger.info(f"Created file metadata for {file_id}: {request.filename}")
        return file_id, upload_url, expires_at

    @staticmethod
    async def confirm_upload(
        db: AsyncIOMotorDatabase,
        file_id: str,
        user_id: str,
    ) -> Optional[dict]:
        """Confirm file upload and verify S3 upload"""
        # Get file metadata
        file_doc = await db.files.find_one({"_id": file_id})
        if not file_doc:
            return None

        # Verify uploader
        if file_doc["uploader_id"] != user_id:
            raise PermissionError("Only the uploader can confirm the upload")

        # Verify file was uploaded to S3
        if not verify_file_uploaded(file_doc["s3_key"]):
            raise ValueError("File not found in S3. Upload may have failed.")

        # Update metadata
        update_result = await db.files.update_one(
            {"_id": file_id},
            {
                "$set": {
                    "uploaded_at": datetime.utcnow(),
                    "virus_scan_status": VirusScanStatus.CLEAN.value,  # Simplified - no actual scan
                }
            }
        )

        if update_result.modified_count == 0:
            return None

        # Get updated document
        file_doc = await db.files.find_one({"_id": file_id})

        # Publish Kafka event
        await publish_event(
            topic=KafkaTopic.FILES,
            event_type=EventType.FILE_UPLOADED,
            data={
                "file_id": file_id,
                "workspace_id": file_doc["workspace_id"],
                "channel_id": file_doc.get("channel_id"),
                "dm_id": file_doc.get("dm_id"),
                "uploader_id": file_doc["uploader_id"],
                "filename": file_doc["filename"],
                "content_type": file_doc["content_type"],
                "size_bytes": file_doc["size_bytes"],
            },
            key=file_id,
        )

        logger.info(f"File upload confirmed: {file_id}")
        return file_doc

    @staticmethod
    async def get_download_url(
        db: AsyncIOMotorDatabase,
        file_id: str,
        user_id: str,
    ) -> tuple[str, datetime]:
        """
        Get presigned download URL

        Returns:
            Tuple of (download_url, expires_at)
        """
        # Get file metadata
        file_doc = await db.files.find_one({"_id": file_id})
        if not file_doc:
            raise ValueError("File not found")

        # Check virus scan status
        if file_doc["virus_scan_status"] == VirusScanStatus.INFECTED.value:
            raise PermissionError("File is infected and cannot be downloaded")

        # Check if upload was confirmed
        if not file_doc.get("uploaded_at"):
            raise ValueError("File upload not confirmed")

        # Generate presigned download URL
        download_url, expires_at = generate_presigned_download_url(file_doc["s3_key"])

        logger.info(f"Generated download URL for file: {file_id}")
        return download_url, expires_at

    @staticmethod
    async def get_metadata(
        db: AsyncIOMotorDatabase,
        file_id: str,
    ) -> Optional[dict]:
        """Get file metadata"""
        file_doc = await db.files.find_one({"_id": file_id})
        if not file_doc:
            return None

        return file_doc

    @staticmethod
    async def delete_file(
        db: AsyncIOMotorDatabase,
        file_id: str,
        user_id: str,
        is_admin: bool = False,
    ) -> bool:
        """Delete file (soft delete in DB, actual delete from S3)"""
        # Get file metadata
        file_doc = await db.files.find_one({"_id": file_id})
        if not file_doc:
            return False

        # Verify permissions
        if file_doc["uploader_id"] != user_id and not is_admin:
            raise PermissionError("Only the uploader or admin can delete the file")

        # Delete from S3
        if file_doc.get("s3_key"):
            delete_file_from_s3(file_doc["s3_key"])

        # Mark as deleted in MongoDB (soft delete)
        await db.files.update_one(
            {"_id": file_id},
            {
                "$set": {
                    "deleted_at": datetime.utcnow(),
                    "deleted_by": user_id,
                }
            }
        )

        # Publish Kafka event
        await publish_event(
            topic=KafkaTopic.FILES,
            event_type=EventType.FILE_DELETED,
            data={
                "file_id": file_id,
                "workspace_id": file_doc["workspace_id"],
                "channel_id": file_doc.get("channel_id"),
                "dm_id": file_doc.get("dm_id"),
                "deleted_by": user_id,
            },
            key=file_id,
        )

        logger.info(f"File deleted: {file_id} by user {user_id}")
        return True

    @staticmethod
    async def list_channel_files(
        db: AsyncIOMotorDatabase,
        channel_id: str,
        limit: int = 50,
    ) -> list[dict]:
        """List files in a channel"""
        cursor = db.files.find(
            {
                "channel_id": channel_id,
                "deleted_at": {"$exists": False},
                "uploaded_at": {"$exists": True, "$ne": None},
            }
        ).sort("created_at", -1).limit(limit)

        return await cursor.to_list(length=limit)
