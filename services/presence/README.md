# Presence Service

Real-time presence tracking and typing indicators via WebSockets.

## Responsibilities

- **WebSocket Management** - Handle WebSocket connections
- **Presence Tracking** - Online, away, offline status
- **Typing Indicators** - Show who is typing in channels
- **Heartbeat** - Keep-alive for connections
- **Room Subscriptions** - Subscribe to channel/DM events

## Technology Stack

- **FastAPI (ASGI)** - WebSocket server
- **Redis Pub/Sub** - Real-time message broadcasting
- **Redis** - Presence state storage (with TTL)

## WebSocket Protocol

**Client → Server:**
```json
{"type": "subscribe", "channel_id": "uuid"}
{"type": "typing", "channel_id": "uuid"}
{"type": "ping"}
```

**Server → Client:**
```json
{"type": "message", "data": {...}}
{"type": "typing", "channel_id": "uuid", "user_id": "uuid"}
{"type": "presence", "user_id": "uuid", "status": "online"}
{"type": "pong"}
```

## Redis Data Structures

- `presence:{user_id}` - Hash with status, last_seen, connection_id (TTL: 5 min)
- `typing:{channel_id}` - Set of user IDs currently typing (TTL: 5 sec)
- `ws:channel:{channel_id}` - Set of connection IDs subscribed to channel

## Development

```bash
cd services/presence
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8007

# Test with wscat
wscat -c "ws://localhost:8007/ws?token=<jwt>"
```

## Status

🚧 **Under Development** - Placeholder service
