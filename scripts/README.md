# CoLink Scripts

Utility scripts for development, testing, and operations.

## Available Scripts

### Service Management

#### `start_services.sh`

Start all CoLink services for local development.

```bash
./scripts/start_services.sh
```

Features:
- Starts all infrastructure services (Docker Compose)
- Starts all backend services (FastAPI)
- Creates log files in `logs/` directory
- Creates PID files for process management

#### `stop_services.sh`

Stop all running CoLink services.

```bash
./scripts/stop_services.sh
```

Features:
- Stops all backend services gracefully
- Stops Docker Compose infrastructure
- Cleans up PID files

### Authentication & Testing

#### `create_test_user.sh`

Create a test user in Keycloak via Admin API.

```bash
./scripts/create_test_user.sh
```

Interactive prompts for:
- Username
- Email
- First Name
- Last Name
- Password
- Admin role (yes/no)

**Prerequisites:**
- Keycloak running (`docker-compose up keycloak`)
- `jq` installed (`apt install jq` or `brew install jq`)

**Example:**

```bash
$ ./scripts/create_test_user.sh

═══════════════════════════════════════════════
  Keycloak Test User Creator
═══════════════════════════════════════════════

Username: alice
Email: alice@example.com
First Name: Alice
Last Name: Smith
Password: ********
Is Admin? (y/n): y

✓ User created successfully!
```

#### `test_auth.py`

Test authentication flow end-to-end.

```bash
python3 scripts/test_auth.py
```

**Prerequisites:**
- Python 3.11+
- Dependencies: `pip install httpx`
- Keycloak running
- API Gateway running
- Test user created

**Tests:**
1. Keycloak connectivity
2. Token acquisition (OAuth2 password grant)
3. API Gateway health
4. Protected endpoint access (`/auth/me`)
5. Admin endpoint access (`/admin/stats`)
6. Invalid token rejection

**Example:**

```bash
$ python3 scripts/test_auth.py

══════════════════════════════════════════════════════════════════════
CoLink Authentication Test Suite
══════════════════════════════════════════════════════════════════════

ℹ Test 1: Checking Keycloak connectivity...
✓ Keycloak realm 'colink' is accessible
  Realm: colink
  Issuer: http://localhost:8080/realms/colink

ℹ Test 3: Checking API Gateway connectivity...
✓ API Gateway is healthy
  Status: healthy
  Service: gateway

ℹ Enter test user credentials:
⚠ Note: Create a test user in Keycloak Admin Console first
ℹ Keycloak Admin: http://localhost:8080 (admin/admin)

  Username: alice
  Password: ********

ℹ Test 2: Acquiring token for user 'alice'...
✓ Token acquired successfully
  Access Token: eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIi...
  Token Type: Bearer
  Expires In: 3600 seconds

ℹ Test 4: Accessing protected endpoint /auth/me...
✓ Protected endpoint accessed successfully
  User ID: 8c3f4d5e-1234-5678-90ab-cdef12345678
  Username: alice
  Email: alice@example.com
  Roles: ['user', 'admin']
  Is Admin: True

ℹ Test 5: Accessing admin endpoint /admin/stats...
✓ Admin endpoint accessed successfully
  Message: Admin stats endpoint
  Admin User: alice

ℹ Test 6: Testing with invalid token...
✓ Invalid token correctly rejected (401)

══════════════════════════════════════════════════════════════════════
✓ All tests completed!
══════════════════════════════════════════════════════════════════════
```

## Dependencies

### Required for Scripts

- **Bash** 4.0+ (for shell scripts)
- **Python** 3.11+ (for Python scripts)
- **Docker & Docker Compose** (for infrastructure)
- **jq** (for JSON processing in shell scripts)
- **curl** (for API calls)

### Python Dependencies

```bash
pip install httpx
```

Or install from requirements file:

```bash
pip install -r requirements-dev.txt
```

## Environment Variables

Scripts use these environment variables (with defaults):

```bash
# Keycloak
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=colink
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin

# Gateway
GATEWAY_URL=http://localhost:8000
```

Override in `.env` file or export before running scripts.

## Troubleshooting

### "Command not found: jq"

Install `jq`:

```bash
# Ubuntu/Debian
sudo apt-get install jq

# macOS
brew install jq

# Alpine
apk add jq
```

### "Cannot connect to Keycloak"

Start Keycloak:

```bash
docker-compose up -d keycloak

# Check logs
docker-compose logs -f keycloak

# Wait for: "Running the server in development mode"
```

### "Cannot connect to API Gateway"

Start the Gateway service:

```bash
cd services/gateway
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### "Failed to get admin token"

Verify Keycloak admin credentials:

```bash
# Default development credentials
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin

# Check if Keycloak is ready
curl http://localhost:8080/realms/colink
```

### "Invalid credentials or user doesn't exist"

Create a test user first:

```bash
./scripts/create_test_user.sh
```

Or use Keycloak Admin Console:
- http://localhost:8080
- Login: admin/admin
- Users → Add user

## Best Practices

1. **Always use test users** for development/testing
2. **Never commit passwords** or secrets
3. **Use .env file** for local configuration
4. **Check service health** before running tests
5. **Review logs** in `logs/` directory for debugging

## Adding New Scripts

When adding new scripts:

1. Create script in `scripts/` directory
2. Make executable: `chmod +x scripts/script_name.sh`
3. Add shebang: `#!/bin/bash` or `#!/usr/bin/env python3`
4. Add usage documentation in this README
5. Add error handling and user-friendly output
6. Use colors for better UX (see existing scripts)

## Related Documentation

- [Keycloak Setup Guide](../docs/KEYCLOAK_SETUP.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [Main README](../README.md)
