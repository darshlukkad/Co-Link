"""
Storage utilities for Files Service

Handles S3 client configuration and presigned URL generation.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# S3 Configuration
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", None)  # For LocalStack
S3_BUCKET = os.getenv("S3_BUCKET", "colink-files")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")

# Presigned URL expiration
UPLOAD_URL_EXPIRATION = int(os.getenv("UPLOAD_URL_EXPIRATION", "3600"))  # 1 hour
DOWNLOAD_URL_EXPIRATION = int(os.getenv("DOWNLOAD_URL_EXPIRATION", "300"))  # 5 minutes

# Global S3 client
_s3_client = None


def get_s3_client():
    """Get or create S3 client"""
    global _s3_client

    if _s3_client is None:
        config = Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'} if S3_ENDPOINT_URL else {}
        )

        _s3_client = boto3.client(
            's3',
            endpoint_url=S3_ENDPOINT_URL,
            region_name=S3_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            config=config,
        )

        # Ensure bucket exists (for LocalStack/dev)
        try:
            _s3_client.head_bucket(Bucket=S3_BUCKET)
            logger.info(f"S3 bucket '{S3_BUCKET}' exists")
        except ClientError:
            logger.info(f"Creating S3 bucket '{S3_BUCKET}'")
            try:
                _s3_client.create_bucket(Bucket=S3_BUCKET)
            except ClientError as e:
                logger.error(f"Failed to create bucket: {e}")

    return _s3_client


def generate_s3_key(workspace_id: str, file_id: str, filename: str) -> str:
    """Generate S3 object key"""
    # Structure: workspace_id/YYYY/MM/DD/file_id/filename
    now = datetime.utcnow()
    date_path = now.strftime("%Y/%m/%d")
    return f"{workspace_id}/{date_path}/{file_id}/{filename}"


def generate_presigned_upload_url(
    s3_key: str,
    content_type: str,
    size_bytes: int,
) -> tuple[str, datetime]:
    """
    Generate presigned URL for file upload

    Returns:
        Tuple of (upload_url, expires_at)
    """
    s3_client = get_s3_client()

    try:
        upload_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': s3_key,
                'ContentType': content_type,
                'ContentLength': size_bytes,
            },
            ExpiresIn=UPLOAD_URL_EXPIRATION,
        )

        expires_at = datetime.utcnow() + timedelta(seconds=UPLOAD_URL_EXPIRATION)
        logger.info(f"Generated upload URL for key: {s3_key}")
        return upload_url, expires_at

    except ClientError as e:
        logger.error(f"Failed to generate upload URL: {e}")
        raise


def generate_presigned_download_url(s3_key: str) -> tuple[str, datetime]:
    """
    Generate presigned URL for file download

    Returns:
        Tuple of (download_url, expires_at)
    """
    s3_client = get_s3_client()

    try:
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': s3_key,
            },
            ExpiresIn=DOWNLOAD_URL_EXPIRATION,
        )

        expires_at = datetime.utcnow() + timedelta(seconds=DOWNLOAD_URL_EXPIRATION)
        logger.info(f"Generated download URL for key: {s3_key}")
        return download_url, expires_at

    except ClientError as e:
        logger.error(f"Failed to generate download URL: {e}")
        raise


def verify_file_uploaded(s3_key: str) -> bool:
    """Verify file was successfully uploaded to S3"""
    s3_client = get_s3_client()

    try:
        s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key)
        return True
    except ClientError:
        return False


def delete_file_from_s3(s3_key: str) -> bool:
    """Delete file from S3"""
    s3_client = get_s3_client()

    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
        logger.info(f"Deleted file from S3: {s3_key}")
        return True
    except ClientError as e:
        logger.error(f"Failed to delete file from S3: {e}")
        return False
