# CoLink - Prioritized Backlog

## Overview

This backlog maps the 20-step delivery plan with prioritized, testable items. Each item includes:
- **Priority:** P0 (critical path), P1 (high), P2 (medium), P3 (nice-to-have)
- **Acceptance Criteria:** Clear, testable conditions for completion
- **Dependencies:** Prerequisites from previous steps
- **Estimated Complexity:** S (small), M (medium), L (large), XL (extra-large)

---

## Step 1 — Architecture & Backlog ✓

**Priority:** P0
**Complexity:** M
**Status:** COMPLETED

### Deliverables
- [x] Architecture diagram (Mermaid)
- [x] RACI matrix
- [x] Data model outline
- [x] Technology stack mapping
- [x] Prioritized backlog

### Acceptance Criteria
- ✓ Diagram shows all services, datastores, and data flows
- ✓ RACI clearly assigns ownership for each capability
- ✓ Backlog has 20 steps with acceptance criteria

---

## Step 2 — Monorepo Scaffold

**Priority:** P0
**Complexity:** M
**Dependencies:** None

### User Stories
- As a developer, I want a consistent project structure so I can navigate easily
- As a DevOps engineer, I want containerized services so I can deploy anywhere
- As a team member, I want clear documentation so I can onboard quickly

### Deliverables
- [ ] Directory structure: `/frontend`, `/services/*`, `/infra/*`, `/ops/*`, `/ci`
- [ ] Root `README.md` with getting-started guide
- [ ] `.gitignore`, `.dockerignore`, `.editorconfig`
- [ ] `docker-compose.dev.yml` for local development
- [ ] `.tool-versions` or `.devcontainer` for environment consistency
- [ ] Basic `.github/workflows/lint.yml` for linting

### Acceptance Criteria
1. Directory structure matches specification:
   ```
   /frontend
   /services
     /gateway
     /auth
     /users
     /channels
     /messaging
     /presence
     /files
     /search
     /admin
   /infra
     /docker
     /k8s
     /terraform
   /ops
     /grafana
     /prometheus
   /ci
   /docs
   ```
2. README includes: project overview, tech stack, prerequisites, local setup
3. `docker-compose.dev.yml` exists with placeholder services
4. GitHub Actions lint workflow runs successfully on push
5. Each service has a `README.md` stub

### Test Plan
- Clone repo, run `docker-compose up` (should start without errors)
- Push code, verify GitHub Actions lint passes
- Verify each directory has appropriate `.gitkeep` or README

---

## Step 3 — Keycloak SSO + 2FA (Google/GitHub OIDC)

**Priority:** P0
**Complexity:** L
**Dependencies:** Step 2

### User Stories
- As a user, I want to sign in with Google/GitHub so I don't create another password
- As a user, I want 2FA so my account is secure
- As a developer, I want standardized JWT validation so services trust the identity

### Deliverables
- [ ] Keycloak Docker container with realm config
- [ ] Realm: `colink`
- [ ] Clients: `colink-web`, `colink-api`
- [ ] Identity providers: Google OIDC, GitHub OIDC
- [ ] TOTP 2FA enabled and required
- [ ] Password reset flow configured
- [ ] FastAPI middleware for JWT verification
- [ ] Role mapping: `user`, `admin`

### Acceptance Criteria
1. Keycloak accessible at `http://localhost:8080` (local dev)
2. Google/GitHub login flows work end-to-end (test with real accounts in dev)
3. TOTP setup screen appears after first login
4. JWT issued contains claims: `sub`, `email`, `preferred_username`, `realm_roles`
5. FastAPI middleware validates JWT signature and expiry
6. Invalid/expired tokens return 401 Unauthorized
7. Password reset email sent (using MailHog or similar test SMTP)
8. Admin users have `admin` role in JWT `realm_roles`

### Test Plan
- Start Keycloak: `docker-compose up keycloak`
- Access admin console: `admin/admin` (dev only)
- Create test user, assign `user` role
- Login via Google, verify TOTP prompt
- Call protected API endpoint with JWT, verify 200
- Call protected API endpoint without token, verify 401
- Call protected API endpoint with expired token, verify 401
- Reset password, verify email received

### Configuration Files
- `infra/docker/keycloak/realm-export.json` - realm config
- `services/gateway/app/auth.py` - JWT middleware

---

## Step 4 — API Contracts (OpenAPI-first)

**Priority:** P0
**Complexity:** M
**Dependencies:** Step 2, Step 3

### User Stories
- As a frontend developer, I want OpenAPI specs so I can generate client SDKs
- As a backend developer, I want contract-first design so APIs are consistent
- As a QA engineer, I want Swagger UI so I can test APIs interactively

### Deliverables
- [ ] OpenAPI 3.1 specs for each service:
  - `gateway` - routing, health
  - `users` - CRUD, profiles, status
  - `channels` - CRUD, memberships
  - `messaging` - messages, threads, reactions
  - `files` - upload, download, metadata
  - `search` - messages, files
  - `admin` - moderation, audit logs
- [ ] FastAPI apps with generated routes from specs
- [ ] Swagger UI at `/docs` for each service
- [ ] Unified OpenAPI at Gateway: `/docs` (aggregated)

### Acceptance Criteria
1. Each service has `openapi.yaml` in `services/{service}/openapi.yaml`
2. Specs include:
   - Authentication: `securitySchemes: bearerAuth`
   - Request/response schemas with examples
   - Error responses (400, 401, 403, 404, 500)
3. FastAPI apps serve Swagger UI at `http://localhost:{port}/docs`
4. Gateway aggregates all specs and serves at `/docs`
5. All endpoints return `application/json`
6. Schemas use Pydantic models for validation

### Test Plan
- Generate FastAPI stubs: `datamodel-codegen --input openapi.yaml --output models.py`
- Start each service, access Swagger UI
- Execute sample requests from Swagger UI
- Verify validation errors for invalid payloads (400)
- Verify auth errors for missing token (401)

### Example Endpoints
**Users Service:**
- `GET /users/me` - get current user profile
- `PUT /users/me` - update profile
- `POST /users/me/status` - set status

**Messaging Service:**
- `POST /channels/{channel_id}/messages` - send message
- `GET /channels/{channel_id}/messages` - list messages (paginated)
- `POST /messages/{message_id}/reactions` - add reaction
- `POST /messages/{message_id}/threads` - create thread

---

## Step 5 — Datastores & Migrations

**Priority:** P0
**Complexity:** M
**Dependencies:** Step 2

### User Stories
- As a developer, I want automated migrations so schema changes are reproducible
- As a DBA, I want indexes so queries are fast
- As a tester, I want seed data so I can test features immediately

### Deliverables
- [ ] `docker-compose.dev.yml` updated with Postgres, MongoDB, Redis
- [ ] Alembic setup for Postgres migrations
- [ ] Initial migrations for all tables (users, channels, messages, etc.)
- [ ] Indexes: FTS on messages.content, indexes on foreign keys
- [ ] MongoDB indexes: file metadata, audit logs
- [ ] Seed script: `scripts/seed_data.py`
- [ ] Seed data: 5 users, 3 channels, 50 messages, 10 reactions

### Acceptance Criteria
1. `docker-compose up db` starts Postgres, Mongo, Redis
2. Postgres accessible at `localhost:5432`
3. MongoDB accessible at `localhost:27017`
4. Redis accessible at `localhost:6379`
5. Alembic migrations run: `alembic upgrade head`
6. All tables created with correct schema
7. FTS index exists: `CREATE INDEX idx_messages_fts ON messages USING gin(to_tsvector('english', content))`
8. Seed script runs: `python scripts/seed_data.py`
9. Seed data verifiable: `psql` queries return expected rows

### Test Plan
- Run `docker-compose up db`
- Run `alembic upgrade head`
- Verify tables: `psql -U colink -d colink -c '\dt'`
- Run seed script
- Query data: `SELECT * FROM users;`
- Test FTS: `SELECT * FROM messages WHERE to_tsvector('english', content) @@ to_tsquery('hello');`

### Configuration
- `services/users/alembic.ini`
- `services/users/alembic/env.py`
- `services/users/alembic/versions/*.py`

---

## Step 6 — WebSocket Gateway + Presence/Typing

**Priority:** P0
**Complexity:** L
**Dependencies:** Step 3, Step 5

### User Stories
- As a user, I want to see who's online so I know who's available
- As a user, I want to see typing indicators so I know someone is responding
- As a developer, I want WebSocket connection management so real-time works reliably

### Deliverables
- [ ] FastAPI WebSocket endpoint: `/ws`
- [ ] JWT authentication on WebSocket handshake
- [ ] Redis pub/sub for room subscriptions
- [ ] Presence tracking: online, away, offline (TTL: 5 min)
- [ ] Typing indicators (TTL: 5 sec)
- [ ] Heartbeat/ping-pong for connection health
- [ ] Graceful disconnection and cleanup

### Acceptance Criteria
1. WebSocket connects: `ws://localhost:8001/ws?token={jwt}`
2. Invalid token rejected with close code 4001
3. Client sends: `{"type": "subscribe", "channel_id": "abc"}`
4. Server confirms: `{"type": "subscribed", "channel_id": "abc"}`
5. Presence updated in Redis: `HSET presence:{user_id} status online`
6. Typing event: client sends `{"type": "typing", "channel_id": "abc"}`, other clients receive event
7. Typing indicator expires after 5 seconds
8. Presence TTL refreshed every 60 seconds (heartbeat)
9. Disconnect removes user from presence

### Test Plan
- Use `wscat` or custom test client
- Connect with valid JWT: `wscat -c "ws://localhost:8001/ws?token=..."`
- Send subscribe message
- Open second connection, send typing event, verify first connection receives it
- Disconnect, verify presence removed from Redis: `HGET presence:{user_id} status`

### WebSocket Message Protocol
**Client → Server:**
```json
{"type": "subscribe", "channel_id": "uuid"}
{"type": "unsubscribe", "channel_id": "uuid"}
{"type": "typing", "channel_id": "uuid"}
{"type": "ping"}
```

**Server → Client:**
```json
{"type": "subscribed", "channel_id": "uuid"}
{"type": "message", "data": {...}}
{"type": "typing", "channel_id": "uuid", "user_id": "uuid", "username": "alice"}
{"type": "presence", "user_id": "uuid", "status": "online"}
{"type": "pong"}
```

---

## Step 7 — Messaging Service + Kafka Events

**Priority:** P0
**Complexity:** XL
**Dependencies:** Step 4, Step 5, Step 6

### User Stories
- As a user, I want to send/edit/delete messages so I can communicate
- As a user, I want to reply in threads so conversations stay organized
- As a user, I want to react with emojis so I can express quickly
- As a developer, I want event-driven architecture so services are decoupled

### Deliverables
- [ ] Messaging service API (FastAPI)
- [ ] Kafka producer for events
- [ ] Kafka consumer for events
- [ ] Endpoints:
  - `POST /channels/{channel_id}/messages` - create
  - `PUT /messages/{message_id}` - edit
  - `DELETE /messages/{message_id}` - soft delete
  - `POST /messages/{message_id}/threads` - create thread
  - `POST /messages/{message_id}/reactions` - add reaction
  - `DELETE /reactions/{reaction_id}` - remove reaction
- [ ] Kafka topics: `message.created`, `message.updated`, `reaction.added`
- [ ] Idempotency: message_id as idempotency key
- [ ] Ordering: partition by channel_id

### Acceptance Criteria
1. Create message: `POST /channels/{channel_id}/messages {"content": "Hello"}` returns 201
2. Message stored in Postgres: `messages` table
3. Kafka event published: `message.created` with payload
4. Edit message: `PUT /messages/{id} {"content": "Hi"}` returns 200, sets `edited_at`
5. Delete message: `DELETE /messages/{id}` sets `deleted_at`, content unchanged
6. Thread reply: `POST /messages/{id}/threads {"content": "Reply"}` creates in `thread_messages`
7. Reaction: `POST /messages/{id}/reactions {"emoji": "👍"}` creates in `reactions`
8. Duplicate reaction returns 409 Conflict
9. Consumer processes `message.created`, triggers downstream (e.g., search index update)
10. WebSocket gateway fans out message to subscribed clients

### Test Plan
- Start Messaging service + Kafka: `docker-compose up messaging kafka`
- Send message via Swagger UI
- Verify in Postgres: `SELECT * FROM messages ORDER BY created_at DESC LIMIT 1;`
- Consume Kafka: `kafka-console-consumer --topic message.created`
- Connect WebSocket, subscribe to channel, send message, verify WebSocket receives event
- Edit message, verify `edited_at` updated
- Delete message, verify `deleted_at` set
- Add reaction, verify in DB
- Add duplicate reaction, verify 409

---

## Step 8 — Channels/DMs + Membership/RBAC

**Priority:** P0
**Complexity:** L
**Dependencies:** Step 4, Step 5

### User Stories
- As a user, I want to create channels so I can organize discussions
- As a user, I want private channels so sensitive topics stay restricted
- As a user, I want to DM colleagues so I can have 1:1 conversations
- As an admin, I want role-based permissions so I can control access

### Deliverables
- [ ] Channels service API
- [ ] Endpoints:
  - `POST /channels` - create channel
  - `GET /channels` - list channels (public + member private)
  - `GET /channels/{id}` - get channel details
  - `PUT /channels/{id}` - update channel (owners only)
  - `DELETE /channels/{id}` - archive channel (owners only)
  - `POST /channels/{id}/members` - invite user
  - `DELETE /channels/{id}/members/{user_id}` - remove user
  - `POST /dms` - create DM session
  - `GET /dms` - list DM sessions
- [ ] Authorization: channel owners can invite/remove, admins can moderate
- [ ] Keycloak role integration: `admin`, `user`

### Acceptance Criteria
1. Create channel: `POST /channels {"name": "general", "is_private": false}` returns 201
2. Creator auto-added as owner in `channel_members`
3. List channels: returns public channels + private channels user is member of
4. Non-members cannot GET private channel details (403)
5. Invite user: `POST /channels/{id}/members {"user_id": "uuid"}` returns 200 (owners only)
6. Non-owners cannot invite (403)
7. DM creation: `POST /dms {"participant_ids": ["uuid1", "uuid2"]}` creates `direct_messages` entry
8. Duplicate DM returns existing session (idempotent)
9. Admins can access all channels (bypass membership check)

### Test Plan
- Create channel as `user1`, verify owner role
- List channels as `user1`, verify appears
- List channels as `user2`, verify public only
- Invite `user2` to private channel, verify appears in their list
- Try to delete channel as `user2`, verify 403
- Delete channel as `user1`, verify archived
- Create DM between `user1` and `user2`, verify session created
- Create DM again, verify returns same session

---

## Step 9 — Files Service (S3) + Mongo Metadata

**Priority:** P1
**Complexity:** L
**Dependencies:** Step 4, Step 5

### User Stories
- As a user, I want to upload files so I can share documents/images
- As a user, I want to download files so I can access shared content
- As a developer, I want presigned URLs so uploads/downloads are secure and direct
- As a security engineer, I want virus scanning so malicious files are blocked

### Deliverables
- [ ] Files service API
- [ ] S3 bucket setup (LocalStack for dev, real S3 for prod)
- [ ] Endpoints:
  - `POST /files/upload-url` - get presigned upload URL
  - `POST /files/{file_id}/confirm` - confirm upload complete
  - `GET /files/{file_id}/download-url` - get presigned download URL
  - `GET /files/{file_id}` - get file metadata
  - `DELETE /files/{file_id}` - delete file
- [ ] MongoDB metadata storage
- [ ] Virus scanning (ClamAV or placeholder)
- [ ] File type validation
- [ ] Size limits: 100 MB per file

### Acceptance Criteria
1. Request upload URL: `POST /files/upload-url {"filename": "doc.pdf", "content_type": "application/pdf"}` returns presigned URL
2. Upload file directly to S3 using presigned URL
3. Confirm upload: `POST /files/{file_id}/confirm` updates MongoDB metadata
4. Virus scan runs (async), updates status
5. Infected files return 403 on download
6. Download URL: `GET /files/{file_id}/download-url` returns presigned S3 URL (5 min expiry)
7. Invalid content types rejected (400)
8. Files > 100 MB rejected (413)
9. Delete file: marks as deleted in Mongo, schedules S3 delete (lifecycle policy)
10. Kafka event: `file.uploaded` published on confirm

### Test Plan
- Request upload URL
- Upload file using curl/Postman to presigned URL
- Confirm upload
- Verify metadata in MongoDB: `db.files.findOne({file_id: "..."})`
- Request download URL, download file
- Upload executable, verify virus scan flags it
- Request download for infected file, verify 403

---

## Step 10 — Frontend (React)

**Priority:** P0
**Complexity:** L
**Dependencies:** Step 3, Step 4

### User Stories
- As a user, I want a web app so I can access CoLink from any browser
- As a user, I want SSO login so I don't manage passwords
- As a developer, I want a modern stack so the app is fast and maintainable

### Deliverables
- [ ] Vite + React + TypeScript setup
- [ ] React Router for routing
- [ ] State management: Redux Toolkit or Zustand
- [ ] Auth flow: redirect to Keycloak, handle callback, store tokens
- [ ] Protected routes: redirect to login if unauthenticated
- [ ] UI shell: sidebar (channels/DMs), main content area, profile menu
- [ ] Styling: Tailwind CSS or MUI
- [ ] API client: axios with interceptors for auth

### Acceptance Criteria
1. App runs: `npm run dev` → `http://localhost:5173`
2. Landing page: "Sign in with Google" and "Sign in with GitHub" buttons
3. Click Google, redirect to Keycloak, redirect back with token
4. Token stored in localStorage (or httpOnly cookie if backend supports)
5. Protected route `/app` redirects to login if no token
6. After login, `/app` shows UI shell
7. Sidebar shows "Channels" and "Direct Messages" placeholders
8. Profile menu shows username, "Settings", "Sign Out"
9. Sign out clears token, redirects to landing
10. Token refresh on expiry (silent refresh)

### Test Plan
- Start frontend: `npm run dev`
- Access `http://localhost:5173`
- Sign in with Google
- Verify redirected to `/app`
- Verify sidebar and profile menu visible
- Sign out, verify redirect to landing
- Try accessing `/app` while logged out, verify redirect to login
- Inspect localStorage, verify token present

### Directory Structure
```
frontend/
  src/
    components/
      Sidebar.tsx
      MessageList.tsx
      Composer.tsx
    pages/
      Landing.tsx
      App.tsx
      Login.tsx
    hooks/
      useAuth.ts
      useWebSocket.ts
    store/
      authSlice.ts
      channelsSlice.ts
      messagesSlice.ts
    api/
      client.ts
      channels.ts
      messages.ts
    App.tsx
    main.tsx
```

---

## Step 11 — Realtime UI

**Priority:** P0
**Complexity:** XL
**Dependencies:** Step 6, Step 7, Step 8, Step 10

### User Stories
- As a user, I want to see new messages instantly so conversations feel live
- As a user, I want to see who's typing so I know to wait for a response
- As a user, I want to see who's online so I know who's available
- As a user, I want threaded replies so I can follow conversations

### Deliverables
- [ ] WebSocket connection in React (useWebSocket hook)
- [ ] Channel view: message list, composer, typing indicators, presence
- [ ] DM view: 1:1 message list
- [ ] Thread view: inline or modal
- [ ] Emoji picker for reactions
- [ ] Optimistic updates: show message immediately, confirm when server acks
- [ ] Local caching: store recent messages in Redux/Zustand
- [ ] Auto-scroll to latest message
- [ ] Unread count badges

### Acceptance Criteria
1. Select channel, messages load via API
2. WebSocket connects, subscribes to channel
3. Send message, appears immediately (optimistic), confirmed when server acks
4. Other users' messages appear in real-time
5. Typing indicator shows when someone types
6. Presence badges show online/away/offline
7. Click message, thread drawer opens
8. Reply in thread, appears in thread view
9. Add reaction, emoji count updates
10. Unread badge shows count for channels with new messages

### Test Plan
- Open app as `user1`, join `#general`
- Open app as `user2` (incognito), join `#general`
- Send message as `user1`, verify appears for `user2` instantly
- Type as `user1`, verify typing indicator for `user2`
- Go offline as `user1`, verify presence changes for `user2`
- Reply in thread as `user2`, verify appears for `user1`
- Add reaction as `user1`, verify count updates for both

---

## Step 12 — Search UI + Results Ranking

**Priority:** P1
**Complexity:** M
**Dependencies:** Step 9, Step 10

### User Stories
- As a user, I want to search messages so I can find past conversations
- As a user, I want to search files so I can locate shared documents
- As a user, I want to filter by channel/user/date so results are relevant

### Deliverables
- [ ] Search bar in app header
- [ ] Search API integration
- [ ] Results page: tabs for Messages and Files
- [ ] Message results: highlight matches, show channel/date context
- [ ] File results: show thumbnail, filename, uploader, date
- [ ] Filters: channel, user, date range
- [ ] Ranking: recent messages first, exact matches boosted
- [ ] Pagination

### Acceptance Criteria
1. Type in search bar, results appear (debounced 300ms)
2. Search "hello", returns messages containing "hello"
3. Postgres FTS used: `to_tsvector` and `to_tsquery`
4. Results show channel name, username, timestamp, message snippet
5. Click result, navigate to message (scroll to highlight)
6. Filter by channel, results scoped
7. Filter by date range, results filtered
8. File search returns MongoDB documents
9. Pagination: 20 results per page, "Load More" button
10. No results shows "No matches found"

### Test Plan
- Search "standup", verify messages with "standup" appear
- Filter by #general, verify only general messages
- Search files "report", verify PDF/DOCX files appear
- Click message result, verify navigates and scrolls to message
- Test pagination, verify loads next 20

---

## Step 13 — Admin & Moderation

**Priority:** P2
**Complexity:** M
**Dependencies:** Step 8, Step 10

### User Stories
- As an admin, I want to manage users so I can remove bad actors
- As an admin, I want to view audit logs so I can investigate issues
- As a moderator, I want to delete messages so I can remove spam

### Deliverables
- [ ] Admin service API
- [ ] Admin UI: `/admin` route (admins only)
- [ ] User management: list, view, suspend, delete
- [ ] Message moderation: delete, flag
- [ ] Audit log viewer: filter by user, action, date
- [ ] Keycloak role check: `admin` role required

### Acceptance Criteria
1. Access `/admin` as non-admin, redirected (403)
2. Access `/admin` as admin, shows dashboard
3. User list: paginated, search by email/username
4. Suspend user: `POST /admin/users/{id}/suspend`, user cannot log in
5. Delete message: `DELETE /admin/messages/{id}`, sets `deleted_at`
6. Audit log: shows all moderation actions
7. Kafka event: `moderation.action` published
8. Admins can join any channel (bypass membership)

### Test Plan
- Login as admin user
- Navigate to `/admin`
- Suspend user, verify user cannot log in
- Delete message, verify appears as deleted in UI
- View audit log, verify suspension recorded

---

## Step 14 — Observability

**Priority:** P1
**Complexity:** L
**Dependencies:** All services

### User Stories
- As a DevOps engineer, I want metrics so I can monitor health
- As a developer, I want traces so I can debug slow requests
- As a SRE, I want dashboards so I can detect incidents

### Deliverables
- [ ] Prometheus metrics in each service
- [ ] OpenTelemetry SDK in each service
- [ ] Grafana dashboards:
  - Service health (RED metrics)
  - Infrastructure (nodes, pods)
  - Business KPIs (DAU, messages/sec)
- [ ] Prometheus scrape config
- [ ] Structured JSON logs
- [ ] Log aggregation (Grafana Loki or CloudWatch)

### Acceptance Criteria
1. Each service exposes `/metrics` endpoint
2. Prometheus scrapes all services
3. Metrics include:
   - `http_requests_total{service, endpoint, status}`
   - `http_request_duration_seconds{service, endpoint}`
   - `websocket_connections{service}`
4. Traces captured via OpenTelemetry
5. Grafana dashboards:
   - RED: Rate (req/sec), Errors (%), Duration (p50/p95/p99)
   - Service dependency graph (from traces)
   - Business: DAU, messages/day, file uploads/day
6. Logs formatted as JSON: `{"timestamp": "...", "level": "info", "service": "messaging", "trace_id": "...", "message": "..."}`
7. Logs viewable in Grafana Loki or CloudWatch Logs Insights

### Test Plan
- Access Prometheus: `http://localhost:9090`
- Query: `rate(http_requests_total[5m])`
- Access Grafana: `http://localhost:3000`
- Import dashboard, verify metrics appear
- Generate traffic, verify charts update
- Access Loki, query: `{service="messaging"}`
- Trace a request, verify spans appear

---

## Step 15 — BI for Power BI

**Priority:** P2
**Complexity:** M
**Dependencies:** Step 5, Step 7

### User Stories
- As a product manager, I want DAU/MAU metrics so I can track growth
- As a business analyst, I want engagement metrics so I can optimize features

### Deliverables
- [ ] BI Exporter service (scheduled job)
- [ ] Analytics schema: facts (messages, logins), dimensions (users, channels, dates)
- [ ] ETL: extract from Postgres/Mongo, transform, load to analytics tables
- [ ] Power BI connector: Postgres or export to CSV
- [ ] Sample PBIX: DAU/MAU, messages per channel, retention cohort

### Acceptance Criteria
1. BI Exporter runs daily (cron or Kubernetes CronJob)
2. Analytics tables: `fact_messages`, `fact_logins`, `dim_users`, `dim_channels`, `dim_dates`
3. DAU query: `SELECT COUNT(DISTINCT user_id) FROM fact_logins WHERE date = CURRENT_DATE`
4. MAU query: `SELECT COUNT(DISTINCT user_id) FROM fact_logins WHERE date >= CURRENT_DATE - INTERVAL '30 days'`
5. Power BI connects to Postgres analytics schema
6. Dashboard shows:
   - DAU/MAU trend (line chart)
   - Messages per channel (bar chart)
   - Top users by messages (table)
   - Retention cohort (heatmap)
7. DAX measures for calculations

### Test Plan
- Run BI Exporter: `python services/bi_exporter/run.py`
- Verify analytics tables populated
- Open Power BI, connect to Postgres
- Load sample dashboard
- Verify visuals render correctly

---

## Step 16 — CI/CD (GitHub Actions)

**Priority:** P1
**Complexity:** M
**Dependencies:** Step 2

### User Stories
- As a developer, I want CI so I know tests pass before merge
- As a DevOps engineer, I want CD so deployments are automated
- As a security engineer, I want scanning so vulnerabilities are detected

### Deliverables
- [ ] `.github/workflows/ci.yml` - lint, test, build
- [ ] `.github/workflows/cd.yml` - build images, push to ECR, deploy to EKS
- [ ] OIDC for AWS (no long-lived credentials)
- [ ] Trivy for image scanning
- [ ] Pytest for backend tests
- [ ] Jest for frontend tests

### Acceptance Criteria
1. CI runs on PR: lint, test, build
2. Linting: `ruff` for Python, `eslint` for TypeScript
3. Tests: `pytest` with coverage > 80%, `jest` with coverage > 70%
4. Build: Docker images built for all services
5. Image scan: Trivy detects critical vulnerabilities, fails build
6. CD runs on merge to `main`:
   - Build images
   - Push to ECR
   - Update Kubernetes manifests
   - Deploy to staging
7. Manual approval for production deploy
8. Rollback on failure

### Test Plan
- Create PR, verify CI runs
- Fail a test, verify CI fails
- Fix test, verify CI passes
- Merge to main, verify CD runs
- Verify images pushed to ECR: `aws ecr list-images --repository-name colink-messaging`
- Verify deployment to staging: `kubectl get pods -n colink-staging`

---

## Step 17 — Kubernetes Manifests

**Priority:** P1
**Complexity:** L
**Dependencies:** Step 2

### User Stories
- As a DevOps engineer, I want Kubernetes manifests so I can deploy anywhere
- As a SRE, I want autoscaling so I handle traffic spikes
- As a developer, I want declarative configs so deployments are reproducible

### Deliverables
- [ ] Kubernetes manifests: Namespace, Deployments, Services, Ingress, ConfigMaps, Secrets
- [ ] HorizontalPodAutoscaler for stateless services
- [ ] PersistentVolumeClaims for stateful sets (if any)
- [ ] Ingress with TLS (cert-manager + Let's Encrypt)
- [ ] Resource requests/limits
- [ ] Liveness/readiness probes

### Acceptance Criteria
1. Namespaces: `colink-staging`, `colink-prod`
2. Deployments for all services with replicas: 2 (staging), 3 (prod)
3. Services: ClusterIP for internal, LoadBalancer for Gateway
4. Ingress:
   - `api.colink.example.com` → Gateway
   - `ws.colink.example.com` → WebSocket Gateway
5. TLS certificates issued by cert-manager
6. ConfigMaps for env vars (non-secret)
7. Secrets for DB passwords, API keys (external secrets operator or sealed secrets)
8. HPA: scale 2-10 replicas based on CPU > 70%
9. Probes:
   - Liveness: `/health`
   - Readiness: `/ready`
10. Resource limits: CPU 500m, Memory 512Mi (adjust per service)

### Test Plan
- Apply manifests: `kubectl apply -k infra/k8s/overlays/staging`
- Verify pods running: `kubectl get pods -n colink-staging`
- Verify services: `kubectl get svc -n colink-staging`
- Verify ingress: `kubectl get ingress -n colink-staging`
- Test external access: `curl https://api.colink.example.com/health`
- Scale test: generate load, verify HPA scales up

---

## Step 18 — Terraform (Bonus)

**Priority:** P3
**Complexity:** XL
**Dependencies:** Step 2

### User Stories
- As a DevOps engineer, I want IaC so infrastructure is version-controlled
- As a team, I want reproducible environments so we can spin up/down easily

### Deliverables
- [ ] Terraform modules:
  - `network` - VPC, subnets, NAT, security groups
  - `eks` - EKS cluster, node groups
  - `rds` - Postgres (Multi-AZ)
  - `documentdb` - MongoDB-compatible
  - `elasticache` - Redis (cluster mode)
  - `msk` - Kafka
  - `s3` - Buckets with versioning
  - `iam` - Roles, policies, OIDC provider for GitHub Actions
- [ ] Remote state: S3 + DynamoDB lock
- [ ] Workspaces: `staging`, `prod`
- [ ] Outputs: cluster endpoint, DB endpoints, bucket names

### Acceptance Criteria
1. Terraform init: `terraform init`
2. Plan: `terraform plan -out=plan.tfplan`
3. Apply: `terraform apply plan.tfplan`
4. Resources created:
   - VPC with public/private subnets across 3 AZs
   - EKS cluster with managed node groups (t3.medium)
   - RDS Postgres (db.t3.small, Multi-AZ)
   - ElastiCache Redis (cache.t3.micro)
   - MSK cluster (kafka.t3.small, 3 brokers)
   - S3 bucket with lifecycle policies
5. OIDC provider configured for GitHub Actions IRSA
6. Outputs saved: `terraform output -json > outputs.json`
7. Destroy: `terraform destroy` removes all resources (test in staging)

### Test Plan
- Run Terraform in staging workspace
- Verify resources in AWS Console
- Connect to EKS: `aws eks update-kubeconfig --name colink-staging`
- Deploy app to EKS, verify works
- Destroy staging, verify clean teardown

---

## Step 19 — Interop Bridge (Stretch)

**Priority:** P3
**Complexity:** L
**Dependencies:** Step 7, Step 8

### User Stories
- As a user, I want to bridge with Slack so I can chat with external teams
- As a developer, I want a generic adapter so we can support multiple platforms

### Deliverables
- [ ] Bridge service (FastAPI)
- [ ] Adapter interface: `send_message`, `receive_message`, `map_user`, `map_channel`
- [ ] Slack adapter: webhooks + Slack API
- [ ] ID translation: CoLink user ↔ Slack user
- [ ] Message format mapping
- [ ] Rate limiting: respect Slack API limits

### Acceptance Criteria
1. Bridge service runs: `docker-compose up bridge`
2. Configure Slack webhook: `POST /bridge/slack/configure {"webhook_url": "...", "token": "..."}`
3. Message sent in CoLink channel, appears in Slack channel
4. Message sent in Slack channel, appears in CoLink channel
5. User mapping: CoLink `@alice` → Slack `@alice`
6. Rate limiting: 1 req/sec to Slack API
7. Error handling: retry on 429, log on 500

### Test Plan
- Configure bridge with Slack workspace
- Send message in CoLink, verify appears in Slack
- Send message in Slack, verify appears in CoLink
- Send 10 messages rapidly, verify rate limiting
- Disable Slack token, verify error logged

---

## Step 20 — Final QA & Hardening

**Priority:** P1
**Complexity:** M
**Dependencies:** All steps

### User Stories
- As a QA engineer, I want a checklist so I know what to test
- As a security engineer, I want a security review so vulnerabilities are addressed
- As a SRE, I want a DR plan so we can recover from disasters

### Deliverables
- [ ] Security checklist (OWASP Top 10)
- [ ] Load test script (Locust or k6)
- [ ] Backup/restore runbook
- [ ] Disaster recovery plan
- [ ] Incident response plan
- [ ] Final smoke test suite

### Acceptance Criteria
1. Security checklist completed:
   - [ ] SQL injection: parameterized queries
   - [ ] XSS: input sanitization
   - [ ] CSRF: tokens on state-changing requests
   - [ ] Auth: JWT validation, expiry, refresh
   - [ ] TLS: all external traffic encrypted
   - [ ] Secrets: not in code, use AWS Secrets Manager
   - [ ] Rate limiting: protect against abuse
   - [ ] File upload: virus scan, type validation
   - [ ] CORS: whitelist frontend origin
   - [ ] Logging: no sensitive data logged
2. Load test: 1000 concurrent users, 95% requests < 500ms
3. Backup runbook:
   - Postgres: automated backups, PITR tested
   - S3: versioning enabled, restore tested
   - Kafka: replication factor 3, retention 7 days
4. DR plan: RTO < 1 hour, RPO < 5 minutes
5. Incident response: on-call rotation, escalation path, runbooks

### Test Plan
- Run load test: `k6 run load_test.js`
- Verify performance meets SLA
- Simulate DB failure, restore from backup
- Simulate AZ failure, verify app stays up (Multi-AZ)
- Review security checklist with team
- Conduct tabletop DR exercise

---

## Summary: Priority Buckets

### P0 - Critical Path (MVP)
1. Step 2: Monorepo Scaffold
2. Step 3: Keycloak SSO
3. Step 4: API Contracts
4. Step 5: Datastores
5. Step 6: WebSocket Gateway
6. Step 7: Messaging Service
7. Step 8: Channels/DMs
8. Step 10: Frontend (React)
9. Step 11: Realtime UI

### P1 - High Priority (Production-Ready)
1. Step 9: Files Service
2. Step 14: Observability
3. Step 16: CI/CD
4. Step 17: Kubernetes
5. Step 20: QA & Hardening

### P2 - Medium Priority (Enhanced Features)
1. Step 12: Search UI
2. Step 13: Admin & Moderation
3. Step 15: BI for Power BI

### P3 - Nice-to-Have (Stretch Goals)
1. Step 18: Terraform
2. Step 19: Interop Bridge

---

## Velocity Assumptions

- **Small (S):** 1-2 days
- **Medium (M):** 3-5 days
- **Large (L):** 1-2 weeks
- **Extra-Large (XL):** 2-3 weeks

**Total estimated timeline:** 12-16 weeks (3-4 months) for full build with a team of 3-4 engineers.

---

## Next Steps

With architecture, RACI, and backlog defined, we're ready to proceed to **Step 2: Monorepo Scaffold**.

**Reply 'continue' to proceed.**
