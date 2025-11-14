# API Testing Guide

Guide for testing CoLink APIs using Swagger UI and cURL.

## Prerequisites

1. Start infrastructure:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

2. Create test user:
```bash
./scripts/create_test_user.sh
```

3. Get authentication token:
```bash
TOKEN=$(curl -s -X POST "http://localhost:8080/realms/colink/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=colink-api" \
  -d "client_secret=colink-api-secret-dev-only" \
  -d "username=alice" \
  -d "password=your-password" \
  -d "grant_type=password" \
  | jq -r '.access_token')

echo $TOKEN
```

## Testing with Swagger UI

### Gateway Service (Port 8000)

```bash
cd services/gateway
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Access: **http://localhost:8000/docs**

Endpoints:
- `GET /auth/me` - Get current user
- `GET /admin/stats` - Admin stats (requires admin role)

### Users Service (Port 8001)

```bash
cd services/users
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Access: **http://localhost:8001/docs**

Test endpoints:
1. Click **"Authorize"** button
2. Enter: `Bearer YOUR_TOKEN_HERE`
3. Try endpoints:
   - `GET /users/me` - Get your profile
   - `PUT /users/me` - Update profile
   - `POST /users/me/status` - Set status
   - `GET /users/search?q=alice` - Search users

### Messaging Service (Port 8002)

```bash
cd services/messaging
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

Access: **http://localhost:8002/docs**

Test endpoints:
1. Authorize with Bearer token
2. Try:
   - `POST /channels/{channel_id}/messages` - Send message
   - `GET /channels/{channel_id}/messages` - Get messages
   - `POST /messages/{message_id}/reactions` - Add reaction

## Testing with cURL

### Get Current User Profile

```bash
curl -X GET "http://localhost:8001/users/me" \
  -H "Authorization: Bearer $TOKEN" | jq
```

Expected response:
```json
{
  "user_id": "8c3f4d5e-1234-5678-90ab-cdef12345678",
  "username": "alice",
  "email": "alice@example.com",
  "display_name": "Alice Smith",
  "avatar_url": null,
  "bio": null,
  "timezone": "America/New_York",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": null
}
```

### Update Profile

```bash
curl -X PUT "http://localhost:8001/users/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Alice Smith Updated",
    "bio": "Senior Product Manager",
    "timezone": "America/Los_Angeles"
  }' | jq
```

### Set User Status

```bash
curl -X POST "http://localhost:8001/users/me/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status_text": "In a meeting",
    "status_emoji": "📅",
    "expiry_minutes": 60
  }' | jq
```

### Send Message

```bash
CHANNEL_ID="550e8400-e29b-41d4-a716-446655440000"

curl -X POST "http://localhost:8002/channels/$CHANNEL_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello team! This is a test message.",
    "mentions": [],
    "attachments": []
  }' | jq
```

### Add Reaction

```bash
MESSAGE_ID="660e8400-e29b-41d4-a716-446655440000"

curl -X POST "http://localhost:8002/messages/$MESSAGE_ID/reactions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "emoji": "👍"
  }' | jq
```

## Testing Error Responses

### Missing Token (401)

```bash
curl -X GET "http://localhost:8001/users/me"
```

Expected:
```json
{
  "error": "Missing authentication token",
  "status_code": 401
}
```

### Invalid Token (401)

```bash
curl -X GET "http://localhost:8001/users/me" \
  -H "Authorization: Bearer invalid-token"
```

### Admin Endpoint Without Admin Role (403)

```bash
curl -X GET "http://localhost:8000/admin/stats" \
  -H "Authorization: Bearer $TOKEN"
```

If user is not admin:
```json
{
  "error": "Role 'admin' required",
  "status_code": 403
}
```

## Available Services

| Service | Port | Swagger UI | Status |
|---------|------|------------|--------|
| **Gateway** | 8000 | http://localhost:8000/docs | ✅ Implemented |
| **Users** | 8001 | http://localhost:8001/docs | ✅ Implemented |
| **Messaging** | 8002 | http://localhost:8002/docs | ✅ Implemented |
| **Files** | 8003 | http://localhost:8003/docs | 📋 OpenAPI spec ready |
| **Search** | 8004 | http://localhost:8004/docs | 📋 OpenAPI spec ready |
| **Admin** | 8005 | http://localhost:8005/docs | 📋 OpenAPI spec ready |
| **Channels** | 8006 | http://localhost:8006/docs | 📋 OpenAPI spec ready |
| **Presence** | 8007 | ws://localhost:8007/ws | 🚧 WebSocket service |

## OpenAPI Specifications

All services have complete OpenAPI 3.1 specifications:

```bash
# View OpenAPI spec
curl http://localhost:8001/openapi.json | jq

# Download spec
curl http://localhost:8001/openapi.json > users-api.json
```

## Generating Client SDKs

Use the OpenAPI specs to generate client SDKs:

### TypeScript/JavaScript

```bash
npx @openapitools/openapi-generator-cli generate \
  -i http://localhost:8001/openapi.json \
  -g typescript-fetch \
  -o ./frontend/src/api/users
```

### Python

```bash
pip install datamodel-code-generator

datamodel-code-generator \
  --input http://localhost:8001/openapi.json \
  --output client/users_models.py
```

## Troubleshooting

### Service won't start

```bash
# Check if port is already in use
lsof -i :8001

# Kill process
kill -9 <PID>
```

### Import errors

```bash
# Install common auth module
cd services/common/auth
pip install -r requirements.txt

# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### JWT verification fails

- Verify Keycloak is running: `docker-compose ps keycloak`
- Check `KEYCLOAK_URL` environment variable
- Ensure token hasn't expired (1 hour lifetime)
- Get fresh token if needed

## Next Steps

- Implement database persistence
- Add Kafka event publishing
- Implement remaining services (Files, Search, Admin, Channels)
- Add comprehensive test suites
- Set up CI/CD for API testing
