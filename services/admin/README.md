# Admin Service

Administration and moderation features for CoLink.

## Responsibilities

- **User Management** - List, suspend, delete users (admin only)
- **Content Moderation** - Delete messages, moderate channels
- **Audit Logging** - Track admin actions in MongoDB
- **RBAC Enforcement** - Require `admin` role from Keycloak
- **Analytics** - Basic admin dashboard metrics

## Technology Stack

- **FastAPI** - Web framework
- **PostgreSQL** - User and channel data
- **MongoDB** - Audit logs
- **Kafka** - Moderation events

## API Endpoints

- `GET /admin/users` - List users (paginated)
- `POST /admin/users/{user_id}/suspend` - Suspend user
- `POST /admin/users/{user_id}/activate` - Activate user
- `DELETE /admin/users/{user_id}` - Delete user
- `DELETE /admin/messages/{message_id}` - Delete message
- `GET /admin/audit-log` - Get audit log (paginated)

## Kafka Topics

**Produces:**
- `moderation.action`

## MongoDB Schema

Collection: `admin_audit`
```json
{
  "audit_id": "uuid",
  "action_type": "suspend_user|delete_message|...",
  "actor_id": "uuid",
  "target_id": "uuid",
  "details": {},
  "timestamp": "datetime"
}
```

## Authorization

All endpoints require:
- Valid JWT with `admin` role in `realm_roles`

Enforced via FastAPI dependency:
```python
async def require_admin(token: str = Depends(get_current_user)):
    if "admin" not in token.get("realm_roles", []):
        raise HTTPException(status_code=403, detail="Admin role required")
```

## Development

```bash
cd services/admin
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8005
pytest
```

## Status

🚧 **Under Development** - Placeholder service
