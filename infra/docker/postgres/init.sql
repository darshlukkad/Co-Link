-- Initialize CoLink PostgreSQL databases
-- This script runs on first container startup

-- Create Keycloak database (separate from main app database)
CREATE DATABASE keycloak;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE colink TO colink;
GRANT ALL PRIVILEGES ON DATABASE keycloak TO colink;

-- Connect to colink database
\c colink

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For trigram text search

-- Create initial schema version tracking table
CREATE TABLE IF NOT EXISTS schema_version (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description)
VALUES ('0.1.0', 'Initial database setup')
ON CONFLICT (version) DO NOTHING;

-- Placeholder: actual schema will be created by Alembic migrations
