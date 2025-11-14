# Files Service

File upload, download, and metadata management using S3.

## Responsibilities

- **Presigned URLs** - Generate S3 presigned URLs for direct upload/download
- **File Metadata** - Store file info in MongoDB
- **Virus Scanning** - Optional virus scan integration (ClamAV)
- **File Validation** - Type and size checks
- **File Lifecycle** - Deletion and versioning

## Technology Stack

- **FastAPI** - Web framework
- **AWS S3** - Object storage (LocalStack for dev)
- **MongoDB** - File metadata
- **Kafka** - File events

## API Endpoints

- `POST /files/upload-url` - Get presigned upload URL
- `POST /files/{file_id}/confirm` - Confirm upload complete
- `GET /files/{file_id}/download-url` - Get presigned download URL
- `GET /files/{file_id}` - Get file metadata
- `DELETE /files/{file_id}` - Delete file

## Kafka Topics

**Produces:**
- `file.uploaded`
- `file.deleted`

## MongoDB Schema

Collection: `files`
```json
{
  "file_id": "uuid",
  "workspace_id": "uuid",
  "channel_id": "uuid",
  "uploader_id": "uuid",
  "filename": "string",
  "content_type": "string",
  "size_bytes": "number",
  "s3_bucket": "string",
  "s3_key": "string",
  "virus_scan": {"status": "clean|infected|pending"},
  "created_at": "datetime"
}
```

## Development

```bash
cd services/files
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003

# Use LocalStack for S3
docker-compose up localstack
```

## Status

🚧 **Under Development** - Placeholder service
