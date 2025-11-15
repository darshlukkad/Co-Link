"""CoLink Search Service - Full-text search for messages and files"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from motor.motor_asyncio import AsyncIOMotorDatabase

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from common.auth import init_jwt_handler, get_current_user, UserContext
from common.database import (
    get_postgres_engine,
    get_mongodb,
    init_postgres,
    init_mongodb,
)
from .models import (
    MessageSearchResult,
    MessageSearchResponse,
    FileSearchResult,
    FileSearchResponse,
    UnifiedSearchResponse,
)
from .service import MessageSearchService, FileSearchService, UnifiedSearchService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "colink")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://colink:colink@localhost:5432/colink")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/colink")


def get_pg_db() -> Session:
    """Get PostgreSQL database session"""
    engine = get_postgres_engine()
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def get_mongo_db() -> AsyncIOMotorDatabase:
    """Get MongoDB database"""
    return get_mongodb()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Search Service...")

    # Initialize JWT handler
    init_jwt_handler(KEYCLOAK_URL, KEYCLOAK_REALM)

    # Initialize PostgreSQL
    try:
        await init_postgres(POSTGRES_URL)
        logger.info("PostgreSQL initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL: {e}")
        raise

    # Initialize MongoDB
    try:
        await init_mongodb(MONGODB_URL)
        logger.info("MongoDB initialized successfully")

        # Create text index on files collection
        mongo_db = get_mongodb()
        await mongo_db.files.create_index([("filename", "text")])
        logger.info("MongoDB text index created")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}")
        raise

    yield

    # Cleanup
    logger.info("Shutting down Search Service...")


app = FastAPI(
    title="CoLink Search Service API",
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
    return {"status": "healthy", "service": "search"}


@app.get("/search/messages", response_model=MessageSearchResponse, tags=["Search"])
async def search_messages(
    q: str = Query(..., min_length=2, description="Search query"),
    channel_id: Optional[str] = None,
    user_id: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_pg_db),
) -> MessageSearchResponse:
    """Search messages using PostgreSQL full-text search"""
    try:
        messages, total = MessageSearchService.search_messages(
            db=db,
            query=q,
            channel_id=channel_id,
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )

        results = []
        for msg in messages:
            # Generate snippet
            snippet = MessageSearchService.generate_snippet(msg.content, q)

            results.append(
                MessageSearchResult(
                    message_id=str(msg.message_id),
                    channel_id=str(msg.channel_id) if msg.channel_id else None,
                    dm_id=str(msg.dm_id) if msg.dm_id else None,
                    user_id=msg.user_id,
                    username="",  # TODO: Fetch from user service
                    content=msg.content,
                    content_snippet=snippet,
                    created_at=msg.created_at,
                )
            )

        return MessageSearchResponse(
            results=results,
            total=total,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to search messages")


@app.get("/search/files", response_model=FileSearchResponse, tags=["Search"])
async def search_files(
    q: str = Query(..., min_length=2, description="Search query"),
    channel_id: Optional[str] = None,
    content_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: UserContext = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> FileSearchResponse:
    """Search files using MongoDB text search"""
    try:
        files, total = await FileSearchService.search_files(
            db=db,
            query=q,
            channel_id=channel_id,
            content_type=content_type,
            limit=limit,
            offset=offset,
        )

        results = [
            FileSearchResult(
                file_id=file.get("file_id"),
                filename=file.get("filename"),
                content_type=file.get("content_type"),
                size_bytes=file.get("size_bytes"),
                uploader_id=file.get("uploader_id"),
                channel_id=file.get("channel_id"),
                dm_id=file.get("dm_id"),
                created_at=file.get("created_at"),
                relevance_score=file.get("score"),
            )
            for file in files
        ]

        return FileSearchResponse(
            results=results,
            total=total,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        raise HTTPException(status_code=500, detail="Failed to search files")


@app.get("/search", response_model=UnifiedSearchResponse, tags=["Search"])
async def unified_search(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    user: UserContext = Depends(get_current_user),
    pg_db: Session = Depends(get_pg_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> UnifiedSearchResponse:
    """Unified search across messages and files"""
    try:
        messages, files, total_messages, total_files = await UnifiedSearchService.unified_search(
            pg_db=pg_db,
            mongo_db=mongo_db,
            query=q,
            limit=limit,
        )

        # Convert messages to results
        message_results = []
        for msg in messages:
            snippet = MessageSearchService.generate_snippet(msg.content, q)
            message_results.append(
                MessageSearchResult(
                    message_id=str(msg.message_id),
                    channel_id=str(msg.channel_id) if msg.channel_id else None,
                    dm_id=str(msg.dm_id) if msg.dm_id else None,
                    user_id=msg.user_id,
                    username="",  # TODO: Fetch from user service
                    content=msg.content,
                    content_snippet=snippet,
                    created_at=msg.created_at,
                )
            )

        # Convert files to results
        file_results = [
            FileSearchResult(
                file_id=file.get("file_id"),
                filename=file.get("filename"),
                content_type=file.get("content_type"),
                size_bytes=file.get("size_bytes"),
                uploader_id=file.get("uploader_id"),
                channel_id=file.get("channel_id"),
                dm_id=file.get("dm_id"),
                created_at=file.get("created_at"),
                relevance_score=file.get("score"),
            )
            for file in files
        ]

        return UnifiedSearchResponse(
            messages=message_results,
            files=file_results,
            total_messages=total_messages,
            total_files=total_files,
        )
    except Exception as e:
        logger.error(f"Error in unified search: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform unified search")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)
