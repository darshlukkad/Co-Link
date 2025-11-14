# API Gateway Service

The API Gateway is the central entry point for all CoLink API requests. It handles routing, authentication, authorization, rate limiting, and request aggregation.

## Responsibilities

- **Request Routing** - Route requests to appropriate backend services
- **Authentication** - Validate JWT tokens from Keycloak
- **Authorization** - Enforce role-based access control (RBAC)
- **Rate Limiting** - Protect against abuse using Redis
- **OpenAPI Aggregation** - Serve unified API documentation
- **CORS Handling** - Manage cross-origin requests
- **Request/Response Logging** - Capture API traffic for observability

## Technology Stack

- **FastAPI** - Web framework
- **Python 3.11+**
- **Keycloak** - Identity provider integration
- **Redis** - Rate limiting and caching

## API Endpoints

- `GET /health` - Health check
- `GET /ready` - Readiness check
- `GET /docs` - OpenAPI documentation (Swagger UI)
- `GET /metrics` - Prometheus metrics
- `/api/v1/*` - Proxied to backend services

## Environment Variables

See `.env.example` in project root.

## Development

```bash
# Install dependencies
cd services/gateway
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload --port 8000

# Run tests
pytest

# Lint
ruff check .
black --check .
```

## Docker

```bash
# Build image
docker build -t colink-gateway -f services/gateway/Dockerfile .

# Run container
docker run -p 8000:8000 --env-file .env colink-gateway
```

## Status

🚧 **Under Development** - Placeholder service
