#!/bin/bash

# Initialize LocalStack AWS services for CoLink development
# This script runs when LocalStack is ready

echo "Initializing LocalStack AWS services..."

# Create S3 bucket for file storage
awslocal s3 mb s3://colink-files-dev
awslocal s3api put-bucket-versioning \
  --bucket colink-files-dev \
  --versioning-configuration Status=Enabled

# Set bucket CORS configuration
awslocal s3api put-bucket-cors \
  --bucket colink-files-dev \
  --cors-configuration '{
    "CORSRules": [
      {
        "AllowedOrigins": ["http://localhost:5173"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedHeaders": ["*"],
        "MaxAgeSeconds": 3000
      }
    ]
  }'

# Set bucket lifecycle policy (delete old versions after 30 days)
awslocal s3api put-bucket-lifecycle-configuration \
  --bucket colink-files-dev \
  --lifecycle-configuration '{
    "Rules": [
      {
        "Id": "DeleteOldVersions",
        "Status": "Enabled",
        "NoncurrentVersionExpiration": {
          "NoncurrentDays": 30
        }
      }
    ]
  }'

echo "LocalStack initialization complete!"
echo "S3 bucket: colink-files-dev (versioning enabled)"
