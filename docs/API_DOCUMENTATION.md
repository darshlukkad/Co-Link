# CoLink API Documentation

Complete API reference for all CoLink microservices.

## Overview

CoLink exposes 10 microservices, each with its own REST API. All services follow OpenAPI 3.0 specifications and provide interactive Swagger UI documentation.

## API Gateway

The API Gateway (port 8000) aggregates all services into a unified endpoint.

**Base URL**: `http://localhost:8000`

### Quick Start

```bash
# Health check
curl http://localhost:8000/health

# Get user profile (requires JWT)
curl -H "Authorization: Bearer <token>" http://localhost:8000/users/me

# Send a message
curl -X POST http://localhost:8000/messages \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"channel_id":"123","content":"Hello!"}'
```

## Service Endpoints

| Service | Port | Swagger UI | OpenAPI Spec |
|---------|------|------------|--------------|
| API Gateway | 8000 | http://localhost:8000/docs | http://localhost:8000/openapi.json |
| Users | 8001 | http://localhost:8001/docs | [/services/users/openapi.yaml](../services/users/openapi.yaml) |
| Messaging | 8002 | http://localhost:8002/docs | [/services/messaging/openapi.yaml](../services/messaging/openapi.yaml) |
| Files | 8003 | http://localhost:8003/docs | [/services/files/openapi.yaml](../services/files/openapi.yaml) |
| Search | 8004 | http://localhost:8004/docs | [/services/search/openapi.yaml](../services/search/openapi.yaml) |
| Admin | 8005 | http://localhost:8005/docs | [/services/admin/openapi.yaml](../services/admin/openapi.yaml) |
| Channels | 8006 | http://localhost:8006/docs | [/services/channels/openapi.yaml](../services/channels/openapi.yaml) |
| Gateway (WS) | 8007 | http://localhost:8007/docs | WebSocket events below |
| Presence | 8008 | http://localhost:8008/docs | REST + WebSocket |
| Notifications | 8009 | http://localhost:8009/docs | REST API |

## Authentication

All API requests require JWT authentication via Keycloak.

### Getting a Token

```bash
# Login to get JWT token
curl -X POST http://localhost:8080/realms/colink/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=colink-backend" \
  -d "username=user@example.com" \
  -d "password=password"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "..."
}
```

### Using the Token

Include in Authorization header:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..." \
  http://localhost:8000/users/me
```

## API Services

### 1. Users Service (Port 8001)

**Purpose**: User management, profiles, authentication

#### Key Endpoints

```yaml
GET    /users/me                    # Get current user profile
PUT    /users/me                    # Update current user profile
GET    /users/{user_id}             # Get user by ID
GET    /users/search                # Search users
POST   /users/avatar                # Upload avatar
GET    /users/{user_id}/status      # Get online status
PUT    /users/me/preferences        # Update user preferences
```

#### Example: Get Current User

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8001/users/me
```

Response:
```json
{
  "user_id": "usr_123",
  "email": "john@example.com",
  "display_name": "John Doe",
  "avatar_url": "https://cdn.colink.io/avatars/usr_123.jpg",
  "status": "online",
  "timezone": "America/New_York",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Example: Update Profile

```bash
curl -X PUT http://localhost:8001/users/me \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Jane Doe",
    "bio": "Product Manager",
    "timezone": "America/Los_Angeles"
  }'
```

### 2. Messaging Service (Port 8002)

**Purpose**: Messages, threads, reactions

#### Key Endpoints

```yaml
POST   /messages                      # Send message
GET    /messages/{message_id}         # Get message
PUT    /messages/{message_id}         # Edit message
DELETE /messages/{message_id}         # Delete message
POST   /messages/{message_id}/reactions # Add reaction
DELETE /messages/{message_id}/reactions/{emoji} # Remove reaction
GET    /messages/{message_id}/thread  # Get thread replies
POST   /messages/{message_id}/thread  # Reply to thread
```

#### Example: Send Message

```bash
curl -X POST http://localhost:8002/messages \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "ch_123",
    "content": "Hello, team!",
    "message_type": "text"
  }'
```

Response:
```json
{
  "message_id": "msg_456",
  "channel_id": "ch_123",
  "user_id": "usr_123",
  "content": "Hello, team!",
  "message_type": "text",
  "created_at": "2024-01-15T10:30:00Z",
  "reactions": [],
  "thread_reply_count": 0
}
```

#### Example: Add Reaction

```bash
curl -X POST http://localhost:8002/messages/msg_456/reactions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"emoji": "👍"}'
```

### 3. Channels Service (Port 8006)

**Purpose**: Channels, DMs, memberships

#### Key Endpoints

```yaml
GET    /workspaces/{workspace_id}/channels    # List channels
POST   /workspaces/{workspace_id}/channels    # Create channel
GET    /channels/{channel_id}                 # Get channel details
PUT    /channels/{channel_id}                 # Update channel
DELETE /channels/{channel_id}                 # Delete channel
POST   /channels/{channel_id}/members         # Add member
DELETE /channels/{channel_id}/members/{user_id} # Remove member
GET    /channels/{channel_id}/messages        # Get channel messages
POST   /dm                                     # Create DM
GET    /dm                                     # List DMs
```

#### Example: Create Channel

```bash
curl -X POST http://localhost:8006/workspaces/ws_123/channels \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "marketing",
    "description": "Marketing team discussions",
    "is_private": false
  }'
```

Response:
```json
{
  "channel_id": "ch_789",
  "workspace_id": "ws_123",
  "name": "marketing",
  "description": "Marketing team discussions",
  "is_private": false,
  "created_by": "usr_123",
  "created_at": "2024-01-15T10:35:00Z",
  "member_count": 1
}
```

### 4. Files Service (Port 8003)

**Purpose**: File uploads, S3 storage, sharing

#### Key Endpoints

```yaml
POST   /upload/presigned-url       # Get S3 presigned URL
POST   /upload/confirm              # Confirm upload completion
GET    /files/{file_id}             # Get file metadata
GET    /files/{file_id}/download    # Download file
DELETE /files/{file_id}             # Delete file
GET    /workspaces/{workspace_id}/files # List workspace files
```

#### Example: Upload File (2-step process)

Step 1: Get presigned URL
```bash
curl -X POST http://localhost:8003/upload/presigned-url \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "report.pdf",
    "content_type": "application/pdf",
    "size": 1048576,
    "workspace_id": "ws_123"
  }'
```

Response:
```json
{
  "file_id": "file_999",
  "upload_url": "https://s3.amazonaws.com/colink-files/...",
  "expires_at": "2024-01-15T11:00:00Z"
}
```

Step 2: Upload to S3
```bash
curl -X PUT "https://s3.amazonaws.com/colink-files/..." \
  -H "Content-Type: application/pdf" \
  --data-binary @report.pdf
```

Step 3: Confirm upload
```bash
curl -X POST http://localhost:8003/upload/confirm \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"file_id": "file_999"}'
```

### 5. Search Service (Port 8004)

**Purpose**: Full-text search across messages and files

#### Key Endpoints

```yaml
GET    /search                      # Unified search
GET    /search/messages             # Search messages only
GET    /search/files                # Search files only
POST   /search/index                # Reindex content (admin)
```

#### Example: Unified Search

```bash
curl "http://localhost:8004/search?q=project%20deadline&workspace_id=ws_123" \
  -H "Authorization: Bearer <token>"
```

Response:
```json
{
  "query": "project deadline",
  "total_results": 15,
  "messages": [
    {
      "message_id": "msg_101",
      "content": "The project deadline is next Friday",
      "channel_id": "ch_123",
      "user": {
        "user_id": "usr_456",
        "display_name": "Alice"
      },
      "created_at": "2024-01-14T15:00:00Z",
      "relevance_score": 0.95
    }
  ],
  "files": [
    {
      "file_id": "file_202",
      "filename": "project_timeline.xlsx",
      "uploaded_by": "usr_456",
      "created_at": "2024-01-10T09:00:00Z",
      "relevance_score": 0.88
    }
  ]
}
```

### 6. Admin Service (Port 8005)

**Purpose**: User moderation, admin tools

#### Key Endpoints

```yaml
GET    /admin/users                 # List all users
PUT    /admin/users/{user_id}/ban   # Ban user
PUT    /admin/users/{user_id}/unban # Unban user
DELETE /admin/messages/{message_id} # Delete any message
GET    /admin/audit-logs            # View audit logs
GET    /admin/analytics             # Get analytics
```

#### Example: Ban User

```bash
curl -X PUT http://localhost:8005/admin/users/usr_789/ban \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Spam",
    "duration_hours": 24
  }'
```

### 7. Presence Service (Port 8008)

**Purpose**: Online status, typing indicators

#### Key Endpoints

```yaml
POST   /presence/online             # Set online
POST   /presence/away               # Set away
POST   /presence/offline            # Set offline
GET    /presence/users/{user_id}    # Get user status
POST   /typing/start                # Start typing
POST   /typing/stop                 # Stop typing
```

#### Example: Set Status

```bash
curl -X POST http://localhost:8008/presence/online \
  -H "Authorization: Bearer <token>"
```

### 8. Notifications Service (Port 8009)

**Purpose**: Push notifications, email

#### Key Endpoints

```yaml
GET    /notifications               # Get user notifications
PUT    /notifications/{id}/read     # Mark as read
PUT    /notifications/read-all      # Mark all as read
POST   /notifications/preferences   # Update preferences
```

#### Example: Get Notifications

```bash
curl http://localhost:8009/notifications?unread_only=true \
  -H "Authorization: Bearer <token>"
```

Response:
```json
{
  "notifications": [
    {
      "notification_id": "notif_123",
      "type": "mention",
      "title": "Alice mentioned you",
      "message": "Alice mentioned you in #marketing",
      "link": "/channels/ch_123/messages/msg_456",
      "is_read": false,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "unread_count": 5
}
```

## WebSocket Events

### Gateway Service (Port 8007)

Real-time events over WebSocket connection.

#### Connection

```javascript
const socket = io('http://localhost:8007', {
  auth: { token: 'Bearer eyJ...' },
  transports: ['websocket']
})
```

#### Client Events (Emit)

```javascript
// Join a channel
socket.emit('channel:join', { channel_id: 'ch_123' })

// Leave a channel
socket.emit('channel:leave', { channel_id: 'ch_123' })

// Start typing
socket.emit('typing:start', { channel_id: 'ch_123' })

// Stop typing
socket.emit('typing:stop', { channel_id: 'ch_123' })
```

#### Server Events (Listen)

```javascript
// New message
socket.on('message:new', (data) => {
  console.log('New message:', data)
  // { message_id, channel_id, user, content, created_at }
})

// Message updated
socket.on('message:updated', (data) => {
  console.log('Message edited:', data)
  // { message_id, content, is_edited, edited_at }
})

// Message deleted
socket.on('message:deleted', (data) => {
  console.log('Message deleted:', data)
  // { message_id, channel_id }
})

// Reaction added
socket.on('reaction:added', (data) => {
  console.log('Reaction added:', data)
  // { message_id, emoji, user_id }
})

// User typing
socket.on('typing:start', (data) => {
  console.log('User typing:', data)
  // { channel_id, user_id, display_name }
})

// User stopped typing
socket.on('typing:stop', (data) => {
  console.log('User stopped typing:', data)
  // { channel_id, user_id }
})

// User presence changed
socket.on('presence:update', (data) => {
  console.log('Presence update:', data)
  // { user_id, status: 'online'|'away'|'offline' }
})
```

## Error Responses

All services follow consistent error response format:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Channel not found",
    "details": {
      "channel_id": "ch_999"
    }
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid JWT token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `INVALID_REQUEST` | 400 | Invalid request parameters |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate) |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

## Rate Limiting

API requests are rate-limited per user:

- **Standard endpoints**: 100 requests/minute
- **Search endpoints**: 20 requests/minute
- **File uploads**: 10 requests/minute

Rate limit headers in response:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705320000
```

## Pagination

List endpoints support cursor-based pagination:

```bash
GET /channels/{channel_id}/messages?limit=50&cursor=msg_123
```

Response:
```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "msg_456",
    "has_more": true,
    "total": 1250
  }
}
```

## Webhooks

Subscribe to events via webhooks (Admin feature):

```bash
curl -X POST http://localhost:8000/webhooks \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhook",
    "events": ["message.created", "channel.created"],
    "secret": "webhook_secret_key"
  }'
```

Webhook payload:
```json
{
  "event": "message.created",
  "timestamp": "2024-01-15T10:00:00Z",
  "data": {
    "message_id": "msg_789",
    "channel_id": "ch_123",
    "user_id": "usr_456",
    "content": "Hello!"
  },
  "signature": "sha256=..."
}
```

## Interactive API Documentation

### Swagger UI

All services provide interactive Swagger UI:

1. Start the service
2. Navigate to `http://localhost:PORT/docs`
3. Click "Authorize" and enter JWT token
4. Try out endpoints directly

### Postman Collection

Import the Postman collection:

```bash
# Located at: /testing/postman/CoLink-API.postman_collection.json
```

### REST Client

Use VS Code REST Client extension with files in `/testing/rest-client/`

## SDK Examples

### Python

```python
import requests

class CoLinkClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    def send_message(self, channel_id, content):
        response = requests.post(
            f"{self.base_url}/messages",
            headers=self.headers,
            json={"channel_id": channel_id, "content": content}
        )
        return response.json()

# Usage
client = CoLinkClient("http://localhost:8000", "your_jwt_token")
message = client.send_message("ch_123", "Hello, world!")
```

### JavaScript/TypeScript

```typescript
class CoLinkAPI {
  private baseURL: string
  private token: string

  constructor(baseURL: string, token: string) {
    this.baseURL = baseURL
    this.token = token
  }

  async sendMessage(channelId: string, content: string) {
    const response = await fetch(`${this.baseURL}/messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ channel_id: channelId, content })
    })
    return response.json()
  }
}

// Usage
const api = new CoLinkAPI('http://localhost:8000', 'your_jwt_token')
const message = await api.sendMessage('ch_123', 'Hello, world!')
```

## Additional Resources

- [OpenAPI Specifications](../services/)
- [WebSocket Events Guide](./WEBSOCKET_EVENTS.md)
- [Authentication Guide](./AUTHENTICATION.md)
- [Development Guide](../DEVELOPMENT.md)

## Support

For API issues:
- Check service logs: `docker-compose logs <service-name>`
- View Swagger UI for endpoint details
- Consult OpenAPI specs for request/response schemas
