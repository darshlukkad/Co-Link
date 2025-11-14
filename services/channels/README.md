# Channels Service

Manages channels, direct messages (DMs), and membership.

## Responsibilities

- **Channel CRUD** - Create, read, update, delete channels
- **Membership Management** - Add/remove users, roles (owner/admin/member)
- **DM Sessions** - Create and manage direct message sessions
- **Channel Discovery** - List public channels
- **Permissions** - Enforce channel-level authorization

## Technology Stack

- **FastAPI** - Web framework
- **PostgreSQL** - Channel and membership data
- **Redis** - Channel metadata caching

## API Endpoints

- `POST /channels` - Create channel
- `GET /channels` - List channels
- `GET /channels/{channel_id}` - Get channel details
- `PUT /channels/{channel_id}` - Update channel
- `DELETE /channels/{channel_id}` - Archive channel
- `POST /channels/{channel_id}/members` - Add member
- `DELETE /channels/{channel_id}/members/{user_id}` - Remove member
- `POST /dms` - Create DM session
- `GET /dms` - List DM sessions

## Database Schema

Tables:
- `channels`
- `channel_members`
- `direct_messages`
- `dm_participants`

## Development

```bash
cd services/channels
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8006
pytest
```

## Status

🚧 **Under Development** - Placeholder service
