# CoLink - Enterprise Chat Application

CoLink is a modern, enterprise-grade chat application similar to Slack, built with a microservices architecture and cloud-native technologies.

## Features

- **Real-time Messaging** - Instant message delivery via WebSockets
- **Channels & Direct Messages** - Organized team communication
- **File Sharing** - Upload and share documents, images, and files
- **Search** - Full-text search across messages and files
- **Threads & Reactions** - Organized conversations with emoji reactions
- **Presence & Typing Indicators** - See who's online and typing
- **SSO Authentication** - Sign in with Google or GitHub via Keycloak
- **2FA Security** - TOTP-based two-factor authentication
- **Admin & Moderation** - User management and content moderation
- **Observability** - Built-in metrics, logs, and distributed tracing

## Technology Stack

### Frontend
- **React.js** with Vite and TypeScript
- **Tailwind CSS** for styling
- **Redux Toolkit** or Zustand for state management
- **WebSocket** client for real-time updates

### Backend
- **Python 3.11+** with FastAPI
- **WebSockets** (ASGI) for real-time communication
- **OpenAPI 3.1** for API documentation
- **Pydantic** for data validation

### Authentication
- **Keycloak** for SSO and identity management
- **OIDC** providers: Google and GitHub
- **TOTP 2FA** for enhanced security
- **JWT** for stateless authentication

### Datastores
- **PostgreSQL 15+** - Users, channels, messages, threads
- **MongoDB 6+** - File metadata and audit logs
- **Redis 7+** - Caching, sessions, presence, pub/sub
- **AWS S3** - File storage with presigned URLs

### Event Streaming
- **Apache Kafka** - Event-driven architecture, async messaging

### Infrastructure
- **Docker** - Containerization
- **Kubernetes (EKS)** - Container orchestration
- **Terraform** - Infrastructure as Code
- **AWS** - Cloud platform

### CI/CD
- **GitHub Actions** - Build, test, and deployment pipelines
- **Trivy** - Container security scanning

### Observability
- **Prometheus** - Metrics collection
- **Grafana** - Dashboards and visualization
- **OpenTelemetry** - Distributed tracing
- **Loki** (optional) - Log aggregation

### Business Intelligence
- **Power BI** - Analytics dashboards for business metrics

## Project Structure

```
colink/
├── frontend/                 # React web application
│   └── src/
│       ├── components/       # Reusable UI components
│       ├── pages/           # Page components
│       ├── hooks/           # Custom React hooks
│       ├── store/           # State management
│       ├── api/             # API client code
│       └── utils/           # Utility functions
│
├── services/                # Backend microservices
│   ├── gateway/            # API Gateway - routing, auth, rate limiting
│   ├── users/              # User profiles and status management
│   ├── channels/           # Channels and DM management
│   ├── messaging/          # Messages, threads, reactions
│   ├── presence/           # Presence and typing indicators
│   ├── files/              # File upload/download, S3 integration
│   ├── search/             # Full-text search for messages and files
│   └── admin/              # Admin and moderation features
│
├── infra/                  # Infrastructure configuration
│   ├── docker/            # Dockerfiles and compose files
│   ├── k8s/               # Kubernetes manifests
│   │   ├── base/          # Base configurations
│   │   └── overlays/      # Environment-specific overlays
│   └── terraform/         # Terraform IaC
│       ├── modules/       # Reusable Terraform modules
│       └── environments/  # Environment configurations
│
├── ops/                    # Operations and observability
│   ├── grafana/           # Grafana dashboards and datasources
│   └── prometheus/        # Prometheus configuration
│
├── ci/                     # CI/CD configuration
│   └── (GitHub Actions workflows stored in .github/workflows/)
│
├── scripts/                # Utility scripts
│   └── seed_data.py       # Database seed script
│
└── docs/                   # Documentation
    ├── ARCHITECTURE.md    # System architecture
    └── BACKLOG.md         # Development backlog

```

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** 24.0+ and **Docker Compose** 2.20+
- **Node.js** 20+ and **npm** 10+
- **Python** 3.11+ and **pip** 23+
- **Git** 2.40+
- **kubectl** 1.28+ (for Kubernetes deployments)
- **Terraform** 1.6+ (optional, for infrastructure provisioning)
- **AWS CLI** 2.13+ (for AWS deployments)

### Optional but Recommended
- **asdf** or **mise** for version management
- **k9s** for Kubernetes cluster management
- **Postman** or **HTTPie** for API testing

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/colink.git
cd colink
```

### 2. Environment Setup

#### Using asdf (Recommended)

```bash
# Install tool versions
asdf install

# Verify installations
python --version  # Should be 3.11+
node --version    # Should be 20+
```

#### Manual Setup

```bash
# Install Python dependencies
pip install -r requirements-dev.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 3. Local Development Environment

#### Start Infrastructure Services

```bash
# Start PostgreSQL, MongoDB, Redis, Kafka, Keycloak
docker-compose up -d
```

This will start:
- **PostgreSQL** on `localhost:5432`
- **MongoDB** on `localhost:27017`
- **Redis** on `localhost:6379`
- **Kafka** on `localhost:9092`
- **Keycloak** on `localhost:8080`
- **Prometheus** on `localhost:9090`
- **Grafana** on `localhost:3000`

#### Verify Services

```bash
# Check all containers are running
docker-compose ps

# Check logs
docker-compose logs -f
```

### 4. Database Setup

```bash
# Run migrations
cd services/users
alembic upgrade head
cd ../..

# Seed development data (optional)
python scripts/seed_data.py
```

### 5. Configure Keycloak

Access Keycloak admin console at `http://localhost:8080`:
- Username: `admin`
- Password: `admin` (development only)

The realm configuration will be imported automatically from `infra/docker/keycloak/realm-export.json`.

### 6. Start Backend Services

```bash
# Terminal 1 - API Gateway
cd services/gateway
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Users Service
cd services/users
uvicorn app.main:app --reload --port 8001

# Terminal 3 - Messaging Service
cd services/messaging
uvicorn app.main:app --reload --port 8002

# Add more services as needed...
```

Or use the provided script:

```bash
# Start all services
./scripts/start_services.sh
```

### 7. Start Frontend

```bash
cd frontend
npm run dev
```

The application will be available at `http://localhost:5173`.

### 8. Access the Application

1. Navigate to `http://localhost:5173`
2. Click "Sign in with Google" or "Sign in with GitHub"
3. Complete authentication and 2FA setup
4. Start chatting!

## API Documentation

Once services are running, access API documentation:

- **API Gateway**: http://localhost:8000/docs
- **Users Service**: http://localhost:8001/docs
- **Messaging Service**: http://localhost:8002/docs
- **Files Service**: http://localhost:8003/docs
- **Search Service**: http://localhost:8004/docs
- **Admin Service**: http://localhost:8005/docs

## Development Workflow

### Running Tests

```bash
# Backend tests
cd services/messaging
pytest

# Frontend tests
cd frontend
npm test

# Run all tests
./scripts/run_tests.sh
```

### Linting & Formatting

```bash
# Python (using ruff)
ruff check .
ruff format .

# TypeScript/JavaScript
cd frontend
npm run lint
npm run format
```

### Building Docker Images

```bash
# Build all services
docker-compose build

# Build specific service
docker build -t colink-messaging -f services/messaging/Dockerfile .
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key environment variables:

```env
# Database
DATABASE_URL=postgresql://colink:colink@localhost:5432/colink
MONGODB_URL=mongodb://localhost:27017/colink
REDIS_URL=redis://localhost:6379

# Keycloak
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=colink
KEYCLOAK_CLIENT_ID=colink-api
KEYCLOAK_CLIENT_SECRET=your-secret-here

# AWS (for production)
AWS_REGION=us-east-1
AWS_S3_BUCKET=colink-files
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Monitoring & Observability

### Prometheus

Access Prometheus at `http://localhost:9090`.

Example queries:
```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Request duration (p95)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Grafana

Access Grafana at `http://localhost:3000`:
- Username: `admin`
- Password: `admin`

Pre-configured dashboards:
- Service Health (RED metrics)
- Infrastructure Overview
- Business KPIs

## Deployment

### Kubernetes

```bash
# Apply base configuration
kubectl apply -k infra/k8s/base

# Apply staging environment
kubectl apply -k infra/k8s/overlays/staging

# Apply production environment
kubectl apply -k infra/k8s/overlays/production
```

### Terraform

```bash
# Initialize Terraform
cd infra/terraform/environments/staging
terraform init

# Plan infrastructure changes
terraform plan -out=plan.tfplan

# Apply changes
terraform apply plan.tfplan
```

## Troubleshooting

### Services won't start

```bash
# Check Docker containers
docker-compose ps

# View logs
docker-compose logs [service-name]

# Restart services
docker-compose restart
```

### Database connection issues

```bash
# Verify database is running
docker-compose ps postgres

# Test connection
psql -h localhost -U colink -d colink

# Check migrations
cd services/users
alembic current
```

### WebSocket connection fails

```bash
# Check WebSocket gateway logs
docker-compose logs gateway

# Verify Redis pub/sub
redis-cli
> PING
> SUBSCRIBE test
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Message Convention

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(messaging): add support for message threads

- Implement thread creation and replies
- Add API endpoints for thread management
- Update WebSocket events for thread updates

Closes #123
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system architecture, data models, and design decisions.

## Backlog & Roadmap

See [docs/BACKLOG.md](docs/BACKLOG.md) for the development backlog and project roadmap.

## Security

- **Authentication**: Keycloak with OIDC and 2FA
- **Authorization**: JWT-based with role-based access control (RBAC)
- **Transport**: TLS/HTTPS for all external traffic
- **Secrets**: AWS Secrets Manager / Kubernetes Secrets
- **Rate Limiting**: Redis-based rate limiting at API Gateway
- **Input Validation**: Pydantic models with strict validation
- **File Security**: Virus scanning, type validation, presigned URLs

### Reporting Security Issues

Please report security vulnerabilities to security@colink.example.com.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/yourusername/colink/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/colink/discussions)

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Keycloak](https://www.keycloak.org/)
- [Kafka](https://kafka.apache.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [Redis](https://redis.io/)

---

**Status**: 🚧 Under Active Development

**Version**: 0.1.0-alpha
