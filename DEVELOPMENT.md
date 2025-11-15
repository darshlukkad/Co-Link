# CoLink Development Guide

Complete guide for setting up and running CoLink locally for development.

## Quick Start

### Option 1: Local Development (Recommended)

Run infrastructure in Docker, services locally:

```bash
# 1. Start infrastructure services
docker-compose -f docker-compose.local.yml up -d

# 2. Install Python dependencies
cd services/users
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Run database migrations
alembic upgrade head

# 4. Start service
uvicorn main:app --reload --port 8001

# 5. Start frontend (in another terminal)
cd frontend
npm install
npm run dev
```

### Option 2: Full Docker

Run everything in Docker:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## Infrastructure Services

### Available Services

| Service | Port | UI Access | Credentials |
|---------|------|-----------|-------------|
| PostgreSQL | 5432 | pgAdmin: http://localhost:5050 | admin@colink.local / admin |
| MongoDB | 27017 | Mongo Express: http://localhost:8081 | admin / admin |
| Redis | 6379 | Redis Commander: http://localhost:8082 | - |
| Kafka | 9092, 29092 | Kafka UI: http://localhost:8080 | - |
| MinIO (S3) | 9000 | Web UI: http://localhost:9001 | minioadmin / minioadmin |

### Service Endpoints

Access database credentials:
- **PostgreSQL**: `postgresql://colink:dev_password@localhost:5432/colink`
- **MongoDB**: `mongodb://colink:dev_password@localhost:27017/colink`
- **Redis**: `redis://:dev_password@localhost:6379/0`
- **Kafka**: `localhost:29092` (from host) or `kafka:9092` (from containers)
- **MinIO**: `http://localhost:9000`

## Backend Services

### Service Architecture

| Service | Port | Purpose | Database |
|---------|------|---------|----------|
| API Gateway | 8000 | Unified REST API | - |
| Users Service | 8001 | User management | PostgreSQL |
| Messaging Service | 8002 | Messages, threads | PostgreSQL |
| Files Service | 8003 | File uploads | MongoDB + S3 |
| Search Service | 8004 | Full-text search | PostgreSQL + MongoDB |
| Admin Service | 8005 | Moderation, admin | PostgreSQL |
| Channels Service | 8006 | Channels, DMs | PostgreSQL |
| Gateway Service | 8007 | WebSocket real-time | Redis |
| Presence Service | 8008 | Online status | Redis |
| Notifications Service | 8009 | Push notifications | PostgreSQL |

### Running Individual Services

Each service can be run independently:

```bash
# Navigate to service directory
cd services/<service-name>

# Create virtual environment (first time only)
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://colink:dev_password@localhost:5432/colink
export REDIS_URL=redis://:dev_password@localhost:6379/0

# Run migrations (if applicable)
alembic upgrade head

# Start service
uvicorn main:app --reload --port 800X
```

### Service Dependencies

```
┌─────────────────┐
│   API Gateway   │  Port 8000
│   (Aggregator)  │
└────────┬────────┘
         │
    ┌────┴────┬─────────┬──────────┬─────────┐
    │         │         │          │         │
┌───▼───┐ ┌──▼──┐  ┌───▼────┐ ┌───▼────┐ ┌─▼──────┐
│ Users │ │Msgs │  │Channels│ │ Files  │ │ Search │
│ 8001  │ │8002 │  │  8006  │ │  8003  │ │  8004  │
└───┬───┘ └──┬──┘  └───┬────┘ └───┬────┘ └────────┘
    │        │         │          │
    └────────┴─────────┴──────────┘
             │
        ┌────▼─────┐
        │  Kafka   │  Event Bus
        └──────────┘
```

## Frontend Development

### Running Frontend

```bash
cd frontend

# Install dependencies (first time)
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Frontend Environment Variables

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=http://localhost:8007
NEXT_PUBLIC_KEYCLOAK_URL=http://localhost:8080
```

### Frontend Structure

```
frontend/
├── app/                 # Next.js pages
│   ├── login/          # Auth pages
│   └── workspace/      # Main app
├── components/         # React components
│   ├── chat/          # Messaging UI
│   ├── sidebar/       # Navigation
│   ├── modals/        # Dialogs
│   └── ui/            # Base components
├── lib/               # Utilities
├── stores/            # Zustand state
└── types/             # TypeScript types
```

## Database Setup

### PostgreSQL Schema

Run migrations for each service:

```bash
# Users service
cd services/users
alembic upgrade head

# Messaging service
cd services/messaging
alembic upgrade head

# ... repeat for other services
```

### Seed Data (Optional)

Create test data:

```bash
cd services/users
python scripts/seed.py
```

## Testing

### Backend Tests

```bash
cd services/<service-name>

# Install test dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# With coverage
pytest --cov=. --cov-report=html
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run E2E tests
npm run test:e2e
```

## Development Workflow

### 1. Start Infrastructure

```bash
docker-compose -f docker-compose.local.yml up -d
```

### 2. Verify Services

Check all infrastructure is healthy:

```bash
docker-compose -f docker-compose.local.yml ps
```

### 3. Run Backend Services

Start services you're working on:

```bash
# Terminal 1: Users service
cd services/users && uvicorn main:app --reload --port 8001

# Terminal 2: Messaging service
cd services/messaging && uvicorn main:app --reload --port 8002

# Terminal 3: API Gateway
cd services/api-gateway && uvicorn main:app --reload --port 8000
```

### 4. Run Frontend

```bash
# Terminal 4: Frontend
cd frontend && npm run dev
```

### 5. Access Application

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database Connection Issues

```bash
# Check PostgreSQL
docker exec -it colink-postgres-dev psql -U colink -d colink

# Check MongoDB
docker exec -it colink-mongodb-dev mongosh -u colink -p dev_password

# Check Redis
docker exec -it colink-redis-dev redis-cli -a dev_password ping
```

### Reset Database

```bash
# Stop services
docker-compose -f docker-compose.local.yml down

# Remove volumes
docker volume rm colink-dev_postgres_dev_data
docker volume rm colink-dev_mongodb_dev_data
docker volume rm colink-dev_redis_dev_data

# Restart
docker-compose -f docker-compose.local.yml up -d
```

### Clear Kafka Topics

```bash
docker exec -it colink-kafka-dev kafka-topics --bootstrap-server localhost:9092 --list
docker exec -it colink-kafka-dev kafka-topics --bootstrap-server localhost:9092 --delete --topic <topic-name>
```

## Environment Variables

### Backend Services (.env)

```env
# Database
DATABASE_URL=postgresql://colink:dev_password@localhost:5432/colink
MONGODB_URL=mongodb://colink:dev_password@localhost:27017/colink
REDIS_URL=redis://:dev_password@localhost:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:29092

# S3/MinIO
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=colink-files

# JWT
JWT_SECRET=dev_jwt_secret_key_change_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# Keycloak
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=colink
KEYCLOAK_CLIENT_ID=colink-backend
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=http://localhost:8007
NEXT_PUBLIC_KEYCLOAK_URL=http://localhost:8080
NEXT_PUBLIC_KEYCLOAK_REALM=colink
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=colink-frontend
```

## Useful Commands

### Docker Compose

```bash
# Start all services
docker-compose -f docker-compose.local.yml up -d

# Stop all services
docker-compose -f docker-compose.local.yml down

# View logs
docker-compose -f docker-compose.local.yml logs -f

# View specific service logs
docker-compose -f docker-compose.local.yml logs -f postgres

# Restart a service
docker-compose -f docker-compose.local.yml restart redis

# Remove everything (including volumes)
docker-compose -f docker-compose.local.yml down -v
```

### Database Commands

```bash
# PostgreSQL shell
docker exec -it colink-postgres-dev psql -U colink -d colink

# MongoDB shell
docker exec -it colink-mongodb-dev mongosh -u colink -p dev_password

# Redis CLI
docker exec -it colink-redis-dev redis-cli -a dev_password
```

### Backend Development

```bash
# Create new migration
cd services/<service>
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Format code
black .
isort .

# Lint
flake8 .
mypy .
```

### Frontend Development

```bash
# Type check
npm run type-check

# Lint
npm run lint

# Format
npm run format

# Build
npm run build
```

## Performance Monitoring

### Database Queries

```sql
-- PostgreSQL: View slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- PostgreSQL: Active connections
SELECT * FROM pg_stat_activity;
```

### Redis Memory

```bash
docker exec -it colink-redis-dev redis-cli -a dev_password INFO memory
```

### Kafka Consumer Lag

Access Kafka UI at http://localhost:8080 to monitor consumer lag.

## IDE Setup

### VS Code

Recommended extensions:
- Python
- Pylance
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- Docker

### Settings (.vscode/settings.json)

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

## Next Steps

1. **Start infrastructure**: `docker-compose -f docker-compose.local.yml up -d`
2. **Run services**: Follow service-specific instructions above
3. **Access UIs**: Check the services table for URLs
4. **Start coding**: Make changes and see them live!

## Additional Resources

- [API Documentation](./docs/api/)
- [Architecture Guide](./docs/architecture.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Contributing Guide](./CONTRIBUTING.md)
