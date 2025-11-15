# Presence Service

Real-time WebSocket gateway for presence tracking, typing indicators, and message broadcasting.

## Overview

The Presence Service provides a WebSocket-based real-time communication layer for CoLink. It handles:

- **WebSocket Connections** - JWT-authenticated persistent connections
- **Presence Tracking** - Online, away, offline status with automatic TTL
- **Typing Indicators** - Real-time typing notifications
- **Room Subscriptions** - Subscribe to channels and DMs for updates
- **Heartbeat Management** - Connection health monitoring
- **Redis Pub/Sub** - Cross-instance message broadcasting

## Architecture

```
┌─────────────┐     WebSocket      ┌──────────────┐
│   Client    │ ◄──────────────► │  Presence    │
│             │   (JWT Auth)       │   Service    │
└─────────────┘                     └──────────────┘
                                           │
                                           ├─► Redis (Presence State)
                                           ├─► Redis Pub/Sub (Broadcast)
                                           └─► Keycloak (JWT Verify)
```

## WebSocket Protocol

### Authentication

Connect with JWT token in query parameter:

```
ws://localhost:8006/ws?token=<JWT_TOKEN>
```

The token is verified against Keycloak's public keys on connection.

### Message Types

#### Client → Server

**Subscribe to Channel/DM**
```json
{
  "type": "subscribe",
  "channel_id": "channel_general"
}

{
  "type": "subscribe",
  "dm_id": "dm_123"
}
```

**Unsubscribe from Channel/DM**
```json
{
  "type": "unsubscribe",
  "channel_id": "channel_general"
}
```

**Typing Indicator**
```json
{
  "type": "typing",
  "channel_id": "channel_general"
}
```

**Heartbeat Ping**
```json
{
  "type": "ping"
}
```

#### Server → Client

**Subscription Confirmed**
```json
{
  "type": "subscribed",
  "channel_id": "channel_general",
  "dm_id": null
}
```

**Unsubscription Confirmed**
```json
{
  "type": "unsubscribed",
  "channel_id": "channel_general"
}
```

**Presence Update**
```json
{
  "type": "presence",
  "user_id": "user-123",
  "username": "alice",
  "status": "online",
  "timestamp": "2025-01-14T12:00:00Z"
}
```

**Typing Broadcast**
```json
{
  "type": "typing",
  "channel_id": "channel_general",
  "dm_id": null,
  "user_id": "user-123",
  "username": "alice"
}
```

**Message Broadcast**
```json
{
  "type": "message",
  "data": {
    "message_id": "msg-456",
    "content": "Hello, world!",
    "user_id": "user-123",
    "channel_id": "channel_general"
  }
}
```

**Heartbeat Pong**
```json
{
  "type": "pong",
  "timestamp": "2025-01-14T12:00:00Z"
}
```

**Error**
```json
{
  "type": "error",
  "error": "Invalid message type",
  "code": 400
}
```

## Redis Data Structures

### Presence Tracking

**Key:** `presence:{user_id}`
**Type:** String (JSON)
**TTL:** 5 minutes

```json
{
  "user_id": "user-123",
  "username": "alice",
  "status": "online",
  "connection_id": "conn-abc",
  "last_seen": "2025-01-14T12:00:00Z"
}
```

Updated on:
- Initial connection
- Every heartbeat ping
- Status change
- Disconnection (set to "offline")

### Typing Indicators

**Key:** `typing:{room_id}:{user_id}`
**Type:** String (username)
**TTL:** 5 seconds

Automatically expires after 5 seconds if not refreshed.

### Pub/Sub Channels

**`presence:updates`** - Broadcast presence changes to all instances
**`message:broadcast`** - Broadcast messages to specific rooms

## Connection Management

### Connection Lifecycle

1. **Connect** - Client opens WebSocket with JWT token
2. **Authenticate** - Server verifies token and extracts user info
3. **Register** - Connection stored in memory, presence set to "online"
4. **Heartbeat** - Client sends ping every 30 seconds
5. **Disconnect** - Connection closed, presence set to "offline"

### Connection Manager

The `ConnectionManager` class handles:

- **Active Connections** - Maps connection_id → ConnectionInfo
- **WebSockets** - Maps connection_id → WebSocket object
- **Room Subscriptions** - Maps room_id → set of connection_ids
- **Broadcasting** - Send messages to all subscribers in a room
- **Pub/Sub Listener** - Receive messages from Redis for cross-instance sync

### Heartbeat & Timeouts

- **Heartbeat Interval:** 30 seconds (configurable)
- **Timeout Threshold:** 2x heartbeat interval (60 seconds)
- **Action:** Connection automatically closed if no ping received

## REST API Endpoints

### Health Check

```
GET /health
```

Returns service health status and active connection count.

**Response:**
```json
{
  "status": "healthy",
  "service": "presence",
  "active_connections": 42
}
```

### Get User Presence

```
GET /presence/{user_id}
```

Get presence status for a specific user.

**Response:**
```json
{
  "user_id": "user-123",
  "username": "alice",
  "status": "online",
  "last_seen": "2025-01-14T12:00:00Z"
}
```

If user is offline (no Redis entry):
```json
{
  "user_id": "user-123",
  "status": "offline",
  "last_seen": null
}
```

### Get All Presence

```
GET /presence
```

Get presence status for all currently online users.

**Response:**
```json
{
  "users": [
    {
      "user_id": "user-123",
      "username": "alice",
      "status": "online",
      "last_seen": "2025-01-14T12:00:00Z"
    },
    {
      "user_id": "user-456",
      "username": "bob",
      "status": "away",
      "last_seen": "2025-01-14T11:55:00Z"
    }
  ],
  "count": 2
}
```

## Configuration

Environment variables:

```bash
# Service
SERVICE_NAME=presence
SERVICE_PORT=8006
LOG_LEVEL=INFO

# Redis
REDIS_URL=redis://:password@redis:6379/0

# Keycloak
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_REALM=colink
KEYCLOAK_CLIENT_ID=colink-api
KEYCLOAK_CLIENT_SECRET=<secret>

# WebSocket
WS_HEARTBEAT_INTERVAL=30      # Seconds
WS_PRESENCE_TTL=300            # 5 minutes
WS_TYPING_TTL=5                # 5 seconds
```

## Development

### Local Development

```bash
cd services/presence

# Install dependencies
pip install -r requirements.txt

# Run service
uvicorn app.main:app --reload --port 8006
```

### With Docker Compose

```bash
# Start all services
docker-compose up -d presence

# View logs
docker-compose logs -f presence

# Restart service
docker-compose restart presence
```

### Testing

#### Automated Test

```bash
cd services/presence
python test_websocket.py auto
```

Runs automated test sequence:
1. Connect to WebSocket
2. Subscribe to #general
3. Send typing indicator
4. Send heartbeat pings
5. Subscribe to #random
6. Unsubscribe from #general
7. Test DM subscriptions

#### Interactive Test

```bash
python test_websocket.py
```

Interactive shell commands:
- `sub <channel_id>` - Subscribe to channel
- `unsub <channel_id>` - Unsubscribe from channel
- `typing <channel_id>` - Send typing indicator
- `ping` - Send heartbeat
- `quit` - Exit

### Using `wscat`

```bash
npm install -g wscat

# Connect (replace <JWT> with actual token)
wscat -c "ws://localhost:8006/ws?token=<JWT>"

# Send messages
> {"type": "subscribe", "channel_id": "channel_general"}
> {"type": "typing", "channel_id": "channel_general"}
> {"type": "ping"}
```

### Getting a JWT Token

For development, get a token from Keycloak:

```bash
# Login to get token
curl -X POST "http://localhost:8080/realms/colink/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=colink-web" \
  -d "username=alice" \
  -d "password=password123" \
  -d "grant_type=password" | jq -r .access_token
```

Or use the API Gateway:

```bash
# After logging in via API Gateway
TOKEN=$(curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}' | jq -r .access_token)

# Connect to WebSocket
wscat -c "ws://localhost:8006/ws?token=$TOKEN"
```

## Monitoring

### Prometheus Metrics

The service exposes metrics at `/metrics` (if enabled):

- `ws_connections_active` - Current active WebSocket connections
- `ws_connections_total` - Total connections created
- `ws_messages_sent` - Messages sent to clients
- `ws_messages_received` - Messages received from clients
- `ws_errors_total` - WebSocket errors

### Logs

Structured logging with levels:

- **INFO** - Connection events, subscriptions, heartbeats
- **WARNING** - Heartbeat timeouts, disconnections
- **ERROR** - Authentication failures, message errors

Example log:
```
2025-01-14 12:00:00 INFO User alice (user-123) connected with connection conn-abc
2025-01-14 12:00:05 INFO Connection conn-abc subscribed to room channel_general
2025-01-14 12:00:30 WARNING No heartbeat from conn-xyz, disconnecting
```

## Security

### Authentication

- **JWT Verification** - All connections must provide valid JWT
- **Token Validation** - Tokens verified against Keycloak public keys
- **Automatic Expiry** - Expired tokens rejected at connection time

### Authorization

- **Room Access** - Future: Verify user has access to channel/DM before subscribing
- **Rate Limiting** - Future: Limit messages per connection per second

### Connection Security

- **TLS/WSS** - Use WSS in production (configured at reverse proxy)
- **Origin Checking** - CORS configured for allowed origins
- **Timeout Protection** - Idle connections automatically closed

## Scaling

### Horizontal Scaling

Multiple instances supported via Redis Pub/Sub:

1. Each instance manages its own WebSocket connections
2. Presence updates published to `presence:updates` channel
3. Message broadcasts published to `message:broadcast` channel
4. All instances subscribe to these channels and broadcast to local connections

### Load Balancing

Use sticky sessions (session affinity) for WebSocket connections:

```nginx
upstream presence {
    ip_hash;  # Sticky sessions based on client IP
    server presence1:8006;
    server presence2:8006;
    server presence3:8006;
}
```

### Redis Clustering

For high availability:
- Use Redis Sentinel for automatic failover
- Or Redis Cluster for sharding
- Adjust connection pool settings in `redis_client.py`

## Troubleshooting

### Connection Refused

- Check service is running: `curl http://localhost:8006/health`
- Verify Redis is accessible: `redis-cli -h localhost -a password ping`
- Check logs: `docker-compose logs presence`

### Authentication Failures

- Verify token is valid: Decode JWT at https://jwt.io
- Check token expiration: `exp` claim must be in future
- Ensure Keycloak is accessible from presence service

### Messages Not Broadcasting

- Check Redis Pub/Sub: `redis-cli PSUBSCRIBE '*'`
- Verify subscriptions: Check connection has subscribed to room
- Review logs for pub/sub listener errors

### High Memory Usage

- Check number of active connections: `GET /health`
- Review connection cleanup on disconnect
- Monitor Redis memory usage
- Consider connection limits per instance

## Future Enhancements

- [ ] **Authorization** - Verify channel/DM access before subscription
- [ ] **Presence Status** - Support "away", "busy", "do not disturb"
- [ ] **Custom Status** - Allow users to set custom status messages
- [ ] **Rate Limiting** - Prevent message flooding
- [ ] **Message Queuing** - Queue messages for offline users
- [ ] **Read Receipts** - Track when users read messages
- [ ] **Delivery Receipts** - Confirm message delivery
- [ ] **Binary Messages** - Support file uploads via WebSocket
- [ ] **Voice/Video Signaling** - WebRTC signaling for calls

## Status

✅ **Implemented** - Step 6 Complete

Key features:
- ✅ WebSocket endpoint with JWT auth
- ✅ Connection manager
- ✅ Redis pub/sub for broadcasting
- ✅ Presence tracking (5-minute TTL)
- ✅ Typing indicators (5-second TTL)
- ✅ Heartbeat and connection health
- ✅ Graceful disconnection
- ✅ REST API for presence queries
- ✅ Docker integration
- ✅ Test client
