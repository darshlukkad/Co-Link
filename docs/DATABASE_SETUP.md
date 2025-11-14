# Database Setup Guide

Complete guide for setting up and managing CoLink databases.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [PostgreSQL Setup](#postgresql-setup)
- [MongoDB Setup](#mongodb-setup)
- [Redis Setup](#redis-setup)
- [Running Migrations](#running-migrations)
- [Seeding Data](#seeding-data)
- [Database Schema](#database-schema)
- [Common Operations](#common-operations)
- [Troubleshooting](#troubleshooting)

## Overview

CoLink uses a polyglot persistence approach:

- **PostgreSQL** - Primary relational data (users, channels, messages)
- **MongoDB** - File metadata, audit logs (document storage)
- **Redis** - Caching, sessions, presence, pub/sub

## Prerequisites

- **Docker & Docker Compose** (for local development)
- **Python 3.11+** with pip
- **psql** client (optional, for direct database access)
- **mongosh** client (optional, for MongoDB access)

## Quick Start

### 1. Start All Databases

```bash
# Start infrastructure services
docker-compose -f docker-compose.dev.yml up -d postgres mongodb redis

# Verify all services are running
docker-compose ps
```

Expected output:
```
colink-postgres    Up    5432/tcp
colink-mongodb     Up    27017/tcp
colink-redis       Up    6379/tcp
```

### 2. Install Dependencies

```bash
# Install Alembic and database drivers
pip install alembic psycopg2-binary pymongo redis sqlalchemy
```

### 3. Run Migrations

```bash
# Navigate to database directory
cd infra/database

# Run migrations
alembic upgrade head
```

### 4. Seed Sample Data

```bash
# From project root
python3 scripts/seed_data.py
```

Done! Your databases are now ready for development.

## PostgreSQL Setup

### Connection Details (Development)

- **Host**: localhost
- **Port**: 5432
- **Database**: colink
- **Username**: colink
- **Password**: colink_dev_password
- **URL**: `postgresql://colink:colink_dev_password@localhost:5432/colink`

### Tables Created

#### Core Tables

1. **workspaces** - Multi-tenancy support
2. **users** - User profiles (cached from Keycloak)
3. **user_status** - Custom user statuses
4. **channels** - Public/private channels
5. **channel_members** - Channel membership with roles
6. **direct_messages** - DM sessions
7. **dm_participants** - DM participants
8. **messages** - All messages (channels + DMs)
9. **threads** - Thread metadata
10. **thread_messages** - Thread replies
11. **reactions** - Emoji reactions
12. **audit_log** - Audit trail

#### Key Features

- **UUID primary keys** for distributed systems
- **Foreign key constraints** for data integrity
- **Indexes** on frequently queried columns
- **Full-text search** on message content (PostgreSQL FTS)
- **Soft deletes** for messages (deleted_at column)
- **Timestamps** with timezone support

### Accessing PostgreSQL

```bash
# Using Docker
docker exec -it colink-postgres psql -U colink -d colink

# Using local psql
psql postgresql://colink:colink_dev_password@localhost:5432/colink
```

### Common Queries

```sql
-- List all tables
\dt

-- Show table schema
\d+ users

-- Count users
SELECT COUNT(*) FROM users;

-- Recent messages
SELECT
    m.message_id,
    m.content,
    u.display_name,
    c.name AS channel,
    m.created_at
FROM messages m
JOIN users u ON m.user_id = u.user_id
LEFT JOIN channels c ON m.channel_id = c.channel_id
ORDER BY m.created_at DESC
LIMIT 10;

-- Full-text search
SELECT message_id, content, created_at
FROM messages
WHERE to_tsvector('english', content) @@ to_tsquery('hello & world')
ORDER BY created_at DESC;

-- Channel statistics
SELECT
    c.name,
    COUNT(DISTINCT cm.user_id) AS members,
    COUNT(m.message_id) AS messages
FROM channels c
LEFT JOIN channel_members cm ON c.channel_id = cm.channel_id
LEFT JOIN messages m ON c.channel_id = m.channel_id
GROUP BY c.channel_id, c.name;
```

## MongoDB Setup

### Connection Details (Development)

- **Host**: localhost
- **Port**: 27017
- **Database**: colink
- **Username**: colink
- **Password**: colink_dev_password
- **URL**: `mongodb://colink:colink_dev_password@localhost:27017/colink?authSource=admin`

### Collections

1. **files** - File metadata with virus scan status
2. **admin_audit** - Admin action audit logs

### Schema Validation

Both collections have JSON Schema validation enforced at the database level.

### Accessing MongoDB

```bash
# Using Docker
docker exec -it colink-mongodb mongosh -u colink -p colink_dev_password --authenticationDatabase admin

# Using local mongosh
mongosh "mongodb://colink:colink_dev_password@localhost:27017/colink?authSource=admin"
```

### Common Operations

```javascript
// Switch to colink database
use colink

// List collections
show collections

// Count files
db.files.countDocuments()

// Find files by uploader
db.files.find({uploader_id: "user-id-here"}).pretty()

// Files uploaded today
db.files.find({
  created_at: {
    $gte: new Date(new Date().setHours(0,0,0,0))
  }
})

// Aggregate file stats
db.files.aggregate([
  {
    $group: {
      _id: "$content_type",
      count: { $sum: 1 },
      total_size: { $sum: "$size_bytes" }
    }
  },
  { $sort: { count: -1 } }
])

// Admin audit log
db.admin_audit.find().sort({timestamp: -1}).limit(10).pretty()
```

## Redis Setup

### Connection Details (Development)

- **Host**: localhost
- **Port**: 6379
- **Password**: colink_dev_password
- **URL**: `redis://:colink_dev_password@localhost:6379/0`

### Key Patterns

- `presence:{user_id}` - User presence data (TTL: 5 min)
- `typing:{channel_id}` - Typing indicators (TTL: 5 sec)
- `session:{session_id}` - User sessions
- `ratelimit:{user_id}:{endpoint}` - Rate limiting counters
- `ws:channel:{channel_id}` - WebSocket subscriptions

### Accessing Redis

```bash
# Using Docker
docker exec -it colink-redis redis-cli -a colink_dev_password

# Using local redis-cli
redis-cli -a colink_dev_password
```

### Common Commands

```bash
# Ping
PING

# List all keys (development only!)
KEYS *

# Get presence
HGETALL presence:user-id-here

# Get typing indicators
SMEMBERS typing:channel-id-here

# Check session
HGETALL session:session-id-here

# Monitor all commands (real-time)
MONITOR

# Get database info
INFO

# Memory usage
MEMORY USAGE presence:user-123
```

## Running Migrations

### Create New Migration

```bash
cd infra/database

# Auto-generate migration (requires models)
alembic revision --autogenerate -m "Add new column"

# Or create empty migration
alembic revision -m "Custom migration"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Show current version
alembic current

# Show migration history
alembic history

# Downgrade one version
alembic downgrade -1
```

### Migration Best Practices

1. **Always review auto-generated migrations** before running
2. **Test migrations** on a copy of production data
3. **Include both upgrade and downgrade** functions
4. **Use transactions** for data migrations
5. **Avoid destructive operations** (dropping columns/tables)
6. **Document breaking changes** in commit messages

## Seeding Data

The seed script creates sample data for development:

```bash
python3 scripts/seed_data.py
```

### What Gets Created

- **1 workspace** - "CoLink Demo"
- **5 users** - Alice, Bob, Charlie, Diana, Eve
- **3 channels** - #general, #random, #engineering
- **1 DM session** - Between Alice and Bob
- **45 messages** - Across channels and DMs
- **1 thread** - With 3 replies
- **~20 reactions** - Various emojis
- **3 audit log entries**

### Custom Seed Data

Edit `scripts/seed_data.py` to customize:

```python
SAMPLE_USERS = [
    {
        'keycloak_id': 'custom-keycloak-id',
        'username': 'myuser',
        'email': 'myuser@example.com',
        'display_name': 'My User',
        'bio': 'Custom bio',
    },
    # ... more users
]
```

## Database Schema

### Entity Relationship Diagram

```
workspaces (1) ──┬── (N) users
                 ├── (N) channels
                 └── (N) direct_messages

users (1) ──┬── (1) user_status
            ├── (N) channel_members
            ├── (N) dm_participants
            ├── (N) messages
            └── (N) reactions

channels (1) ──┬── (N) channel_members
               └── (N) messages

messages (1) ──┬── (1) threads
               ├── (N) reactions
               └── (N) attachments (files)

threads (1) ──── (N) thread_messages
```

### Table Details

**users** table:
- Primary key: `user_id` (Keycloak ID)
- Cached from Keycloak for performance
- Includes display_name, avatar, bio, timezone
- Foreign key to workspace

**messages** table:
- Primary key: `message_id` (UUID)
- References either `channel_id` OR `dm_id` (check constraint)
- Soft delete via `deleted_at`
- Full-text search index on `content`
- Arrays for `mentions` and `attachments`

**reactions** table:
- Composite unique key: (message_id, user_id, emoji)
- Prevents duplicate reactions
- Can react to messages or thread messages

## Common Operations

### Backup Database

```bash
# PostgreSQL
docker exec colink-postgres pg_dump -U colink colink > backup.sql

# MongoDB
docker exec colink-mongodb mongodump -u colink -p colink_dev_password --authenticationDatabase admin --db colink --out /tmp/backup
docker cp colink-mongodb:/tmp/backup ./mongodb-backup
```

### Restore Database

```bash
# PostgreSQL
cat backup.sql | docker exec -i colink-postgres psql -U colink -d colink

# MongoDB
docker cp ./mongodb-backup colink-mongodb:/tmp/restore
docker exec colink-mongodb mongorestore -u colink -p colink_dev_password --authenticationDatabase admin --db colink /tmp/restore/colink
```

### Reset Database

```bash
# WARNING: Destroys all data!

# PostgreSQL
docker exec colink-postgres psql -U colink -d colink -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Re-run migrations
cd infra/database && alembic upgrade head

# MongoDB
docker exec colink-mongodb mongosh -u colink -p colink_dev_password --authenticationDatabase admin --eval "db.getSiblingDB('colink').dropDatabase()"

# Restart MongoDB container to re-run init script
docker-compose restart mongodb

# Redis
docker exec colink-redis redis-cli -a colink_dev_password FLUSHALL
```

## Troubleshooting

### Migration Fails: "relation already exists"

**Problem**: Table already exists from previous setup

**Solution**:
```bash
# Mark current state as migrated
cd infra/database
alembic stamp head
```

### Cannot Connect to PostgreSQL

**Problem**: Connection refused or authentication failed

**Solutions**:
```bash
# Check if container is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Verify connection string
echo $DATABASE_URL

# Test connection
psql postgresql://colink:colink_dev_password@localhost:5432/colink -c "SELECT 1"
```

### Full-Text Search Not Working

**Problem**: FTS queries return no results

**Solution**:
```sql
-- Verify FTS index exists
SELECT indexname FROM pg_indexes WHERE tablename = 'messages';

-- Rebuild FTS index if needed
REINDEX INDEX idx_messages_content_fts;

-- Test FTS directly
SELECT to_tsvector('english', 'hello world') @@ to_tsquery('hello');
```

### MongoDB Authentication Failed

**Problem**: "Authentication failed" error

**Solution**:
```bash
# Use correct auth database
mongosh "mongodb://colink:colink_dev_password@localhost:27017/colink?authSource=admin"

# Or specify in connection
mongosh --host localhost --port 27017 -u colink -p colink_dev_password --authenticationDatabase admin
```

### Redis Connection Timeout

**Problem**: Redis commands hang or timeout

**Solutions**:
```bash
# Check Redis is running
docker-compose ps redis

# Check logs
docker-compose logs redis

# Test connection
redis-cli -h localhost -p 6379 -a colink_dev_password PING
```

## Production Considerations

1. **Use managed services**:
   - AWS RDS for PostgreSQL
   - MongoDB Atlas or AWS DocumentDB
   - AWS ElastiCache for Redis

2. **Enable SSL/TLS** for all database connections

3. **Use connection pooling**:
   - PostgreSQL: PgBouncer or built-in SQLAlchemy pool
   - MongoDB: Built-in connection pool
   - Redis: Connection pool in redis-py

4. **Set up monitoring**:
   - Query performance (slow query logs)
   - Connection pool metrics
   - Disk usage alerts
   - Replication lag (if applicable)

5. **Regular backups**:
   - Automated daily backups
   - Point-in-time recovery (PITR)
   - Test restore procedures
   - Off-site backup storage

6. **Security**:
   - Strong passwords
   - Firewall rules (only allow application servers)
   - Encrypted storage (at rest)
   - Audit logging enabled
   - Regular security patches

## Related Documentation

- [Architecture](./ARCHITECTURE.md)
- [API Testing](./API_TESTING.md)
- [Keycloak Setup](./KEYCLOAK_SETUP.md)

## Support

For issues:
1. Check logs: `docker-compose logs <service>`
2. Verify configuration in `.env`
3. Review this troubleshooting section
4. Check GitHub issues
