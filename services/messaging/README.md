# Messaging Service

Core messaging functionality including messages, threads, and reactions.

## Responsibilities

- **Message CRUD** - Send, edit, delete messages
- **Threads** - Create and manage threaded conversations
- **Reactions** - Add/remove emoji reactions
- **Kafka Events** - Publish message events for real-time delivery
- **Message History** - Paginated message retrieval

## Technology Stack

- **FastAPI** - Web framework
- **PostgreSQL** - Message storage
- **Kafka** - Event streaming
- **Redis** - Message caching (recent messages)

## API Endpoints

- `POST /channels/{channel_id}/messages` - Send message
- `GET /channels/{channel_id}/messages` - Get messages (paginated)
- `PUT /messages/{message_id}` - Edit message
- `DELETE /messages/{message_id}` - Delete message (soft delete)
- `POST /messages/{message_id}/threads` - Create thread
- `POST /messages/{message_id}/reactions` - Add reaction
- `DELETE /reactions/{reaction_id}` - Remove reaction

## Kafka Topics

**Produces:**
- `message.created`
- `message.updated`
- `message.deleted`
- `reaction.added`
- `reaction.removed`

## Database Schema

Tables:
- `messages`
- `threads`
- `thread_messages`
- `reactions`

## Development

```bash
cd services/messaging
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
pytest
```

## Status

🚧 **Under Development** - Placeholder service
