// Initialize CoLink MongoDB database
// This script runs on first container startup

db = db.getSiblingDB('colink');

// Create collections with validation schemas
db.createCollection('files', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['file_id', 'workspace_id', 'uploader_id', 'filename', 'content_type', 'size_bytes', 's3_bucket', 's3_key', 'created_at'],
      properties: {
        file_id: { bsonType: 'string', description: 'UUID of the file' },
        workspace_id: { bsonType: 'string', description: 'UUID of the workspace' },
        channel_id: { bsonType: ['string', 'null'], description: 'UUID of the channel (if applicable)' },
        dm_id: { bsonType: ['string', 'null'], description: 'UUID of the DM session (if applicable)' },
        message_id: { bsonType: ['string', 'null'], description: 'UUID of the message (if applicable)' },
        uploader_id: { bsonType: 'string', description: 'UUID of the user who uploaded' },
        filename: { bsonType: 'string', description: 'Original filename' },
        content_type: { bsonType: 'string', description: 'MIME type' },
        size_bytes: { bsonType: 'long', description: 'File size in bytes' },
        s3_bucket: { bsonType: 'string', description: 'S3 bucket name' },
        s3_key: { bsonType: 'string', description: 'S3 object key' },
        s3_version_id: { bsonType: ['string', 'null'], description: 'S3 version ID' },
        metadata: { bsonType: 'object', description: 'Additional metadata' },
        virus_scan: { bsonType: 'object', description: 'Virus scan results' },
        created_at: { bsonType: 'date', description: 'Upload timestamp' },
        updated_at: { bsonType: 'date', description: 'Last update timestamp' }
      }
    }
  }
});

db.createCollection('admin_audit', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['audit_id', 'action_type', 'actor_id', 'timestamp'],
      properties: {
        audit_id: { bsonType: 'string', description: 'UUID of the audit entry' },
        action_type: { bsonType: 'string', description: 'Type of action performed' },
        actor_id: { bsonType: 'string', description: 'UUID of the user who performed the action' },
        target_id: { bsonType: ['string', 'null'], description: 'UUID of the target entity' },
        details: { bsonType: 'object', description: 'Action details' },
        timestamp: { bsonType: 'date', description: 'Action timestamp' }
      }
    }
  }
});

// Create indexes for performance
db.files.createIndex({ file_id: 1 }, { unique: true });
db.files.createIndex({ workspace_id: 1, created_at: -1 });
db.files.createIndex({ channel_id: 1, created_at: -1 });
db.files.createIndex({ uploader_id: 1, created_at: -1 });
db.files.createIndex({ filename: 'text' });

db.admin_audit.createIndex({ audit_id: 1 }, { unique: true });
db.admin_audit.createIndex({ actor_id: 1, timestamp: -1 });
db.admin_audit.createIndex({ action_type: 1, timestamp: -1 });
db.admin_audit.createIndex({ timestamp: -1 });

print('CoLink MongoDB initialization complete');
