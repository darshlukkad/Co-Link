"""CoLink Files Service - File upload/download with S3"""

import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
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
    UploadUrlRequest,
    UploadUrlResponse,
    DownloadUrlResponse,
    FileMetadata,
    VirusScanStatus,
)
from .service import FileService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "colink")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/colink")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Default workspace ID
DEFAULT_WORKSPACE_ID = os.getenv("DEFAULT_WORKSPACE_ID", "00000000-0000-0000-0000-000000000001")


def get_db() -> AsyncIOMotorDatabase:
    """Get MongoDB database"""
    return get_mongodb()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Files Service...")

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
    logger.info("Shutting down Files Service...")
    await close_kafka_producer()


app = FastAPI(
    title="CoLink Files Service API",
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
    return {"status": "healthy", "service": "files"}


@app.post("/files/upload-url", response_model=UploadUrlResponse, tags=["Files"])
async def get_upload_url(
    request: UploadUrlRequest,
    user: UserContext = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UploadUrlResponse:
    """Get presigned URL for file upload"""
    try:
        # Validate file size
        if request.size_bytes > 104857600:  # 100MB
            raise HTTPException(status_code=413, detail="File too large (max 100MB)")

        # Validate file type (basic validation)
        allowed_types = [
            "image/", "video/", "audio/", "application/pdf",
            "text/", "application/msword", "application/vnd.",
        ]
        if not any(request.content_type.startswith(t) for t in allowed_types):
            raise HTTPException(status_code=400, detail="File type not allowed")

        file_id, upload_url, expires_at = await FileService.create_upload_url(
            db=db,
            workspace_id=DEFAULT_WORKSPACE_ID,
            user_id=user.user_id,
            request=request,
        )

        return UploadUrlResponse(
            file_id=file_id,
            upload_url=upload_url,
            expires_at=expires_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating upload URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to create upload URL")


@app.post("/files/{file_id}/confirm", response_model=FileMetadata, tags=["Files"])
async def confirm_upload(
    file_id: str,
    user: UserContext = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> FileMetadata:
    """Confirm file upload completion"""
    try:
        file_doc = await FileService.confirm_upload(
            db=db,
            file_id=file_id,
            user_id=user.user_id,
        )

        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")

        return FileMetadata(
            file_id=file_doc["file_id"],
            workspace_id=file_doc["workspace_id"],
            channel_id=file_doc.get("channel_id"),
            dm_id=file_doc.get("dm_id"),
            uploader_id=file_doc["uploader_id"],
            filename=file_doc["filename"],
            content_type=file_doc["content_type"],
            size_bytes=file_doc["size_bytes"],
            virus_scan_status=VirusScanStatus(file_doc["virus_scan_status"]),
            s3_bucket=file_doc.get("s3_bucket"),
            s3_key=file_doc.get("s3_key"),
            created_at=file_doc["created_at"],
            uploaded_at=file_doc.get("uploaded_at"),
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to confirm upload")


@app.get("/files/{file_id}/download-url", response_model=DownloadUrlResponse, tags=["Files"])
async def get_download_url(
    file_id: str,
    user: UserContext = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> DownloadUrlResponse:
    """Get presigned URL for file download"""
    try:
        download_url, expires_at = await FileService.get_download_url(
            db=db,
            file_id=file_id,
            user_id=user.user_id,
        )

        return DownloadUrlResponse(
            download_url=download_url,
            expires_at=expires_at,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting download URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to get download URL")


@app.get("/files/{file_id}", response_model=FileMetadata, tags=["Files"])
async def get_file_metadata(
    file_id: str,
    user: UserContext = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> FileMetadata:
    """Get file metadata"""
    try:
        file_doc = await FileService.get_metadata(db=db, file_id=file_id)

        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")

        # Check if deleted
        if file_doc.get("deleted_at"):
            raise HTTPException(status_code=404, detail="File not found")

        return FileMetadata(
            file_id=file_doc["file_id"],
            workspace_id=file_doc["workspace_id"],
            channel_id=file_doc.get("channel_id"),
            dm_id=file_doc.get("dm_id"),
            uploader_id=file_doc["uploader_id"],
            filename=file_doc["filename"],
            content_type=file_doc["content_type"],
            size_bytes=file_doc["size_bytes"],
            virus_scan_status=VirusScanStatus(file_doc["virus_scan_status"]),
            s3_bucket=file_doc.get("s3_bucket"),
            s3_key=file_doc.get("s3_key"),
            created_at=file_doc["created_at"],
            uploaded_at=file_doc.get("uploaded_at"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to get file metadata")


@app.delete("/files/{file_id}", status_code=204, tags=["Files"])
async def delete_file(
    file_id: str,
    user: UserContext = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Delete file"""
    try:
        # TODO: Check if user is admin
        is_admin = False

        success = await FileService.delete_file(
            db=db,
            file_id=file_id,
            user_id=user.user_id,
            is_admin=is_admin,
        )

        if not success:
            raise HTTPException(status_code=404, detail="File not found")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete file")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
