# Users Service

Manages user profiles, status updates, and user-related operations.

## Responsibilities

- **User CRUD** - Create, read, update user profiles
- **Profile Management** - Display name, avatar, bio
- **Status Management** - Custom status text and emoji
- **User Preferences** - Settings and preferences
- **User Search** - Find users by name or email

## Technology Stack

- **FastAPI** - Web framework
- **PostgreSQL** - User data storage
- **Redis** - Profile caching
- **Alembic** - Database migrations

## API Endpoints

- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update current user profile
- `POST /users/me/status` - Set user status
- `GET /users/{user_id}` - Get user by ID
- `GET /users/search` - Search users

## Database Schema

See `alembic/versions/` for migration files.

Tables:
- `users`
- `user_status`

## Development

```bash
cd services/users
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start service
uvicorn app.main:app --reload --port 8001

# Run tests
pytest
```

## Status

🚧 **Under Development** - Placeholder service
