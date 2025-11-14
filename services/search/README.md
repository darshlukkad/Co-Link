# Search Service

Full-text search for messages and file metadata.

## Responsibilities

- **Message Search** - PostgreSQL full-text search (FTS)
- **File Search** - MongoDB text search on metadata
- **Filters** - Channel, user, date range filters
- **Ranking** - Relevance-based result ranking
- **Pagination** - Efficient large result sets

## Technology Stack

- **FastAPI** - Web framework
- **PostgreSQL** - Message FTS using `tsvector`
- **MongoDB** - File metadata search

## API Endpoints

- `GET /search/messages?q={query}` - Search messages
- `GET /search/files?q={query}` - Search files
- `GET /search?q={query}` - Unified search (messages + files)

## Query Parameters

- `q` - Search query
- `channel_id` - Filter by channel
- `user_id` - Filter by user
- `from_date` - Start date
- `to_date` - End date
- `limit` - Results per page (default: 20)
- `offset` - Pagination offset

## PostgreSQL FTS

Uses `to_tsvector` and `to_tsquery` for efficient full-text search:

```sql
SELECT * FROM messages
WHERE to_tsvector('english', content) @@ to_tsquery('hello & world');
```

Index:
```sql
CREATE INDEX idx_messages_fts ON messages
USING gin(to_tsvector('english', content));
```

## Development

```bash
cd services/search
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8004
pytest
```

## Status

🚧 **Under Development** - Placeholder service
