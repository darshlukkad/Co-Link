# CoLink Deployment Guide

This guide provides comprehensive instructions for deploying the CoLink platform across different environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Compose Deployment](#docker-compose-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [AWS EKS Production Setup](#aws-eks-production-setup)
6. [Environment Configuration](#environment-configuration)
7. [Database Migrations](#database-migrations)
8. [Monitoring & Observability](#monitoring--observability)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

- **Docker** (20.10+)
- **Docker Compose** (2.0+)
- **Kubernetes** (1.25+)
- **kubectl** (1.25+)
- **Kustomize** (5.0+)
- **Helm** (3.10+) - optional
- **AWS CLI** (2.0+) - for AWS deployments
- **Python** (3.11+)
- **Node.js** (18+) - for frontend

### Cloud Resources (Production)

- AWS EKS cluster
- RDS PostgreSQL instance (or self-hosted)
- DocumentDB/MongoDB Atlas
- ElastiCache Redis
- Amazon MSK (Kafka) or Confluent Cloud
- S3 bucket for file storage
- Route53 for DNS
- Certificate Manager for TLS

---

## Local Development

### 1. Clone Repository

```bash
git clone https://github.com/your-org/colink.git
cd colink
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your local configuration
```

### 3. Start Infrastructure Services

```bash
# Start PostgreSQL, MongoDB, Redis, Kafka
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be healthy
docker-compose -f docker-compose.dev.yml ps
```

### 4. Run Database Migrations

```bash
# PostgreSQL migrations
cd services/common/database
alembic upgrade head

# MongoDB indexes (if needed)
python scripts/create_mongo_indexes.py
```

### 5. Start Microservices

**Option A: Using the start script**
```bash
./scripts/start_services.sh
```

**Option B: Start services individually**
```bash
# Terminal 1 - Users Service
cd services/users
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Terminal 2 - Messaging Service
cd services/messaging
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002

# ... repeat for other services
```

### 6. Access Services

- **Users Service**: http://localhost:8001/docs
- **Messaging Service**: http://localhost:8002/docs
- **Files Service**: http://localhost:8003/docs
- **Search Service**: http://localhost:8004/docs
- **Admin Service**: http://localhost:8005/docs
- **Channels Service**: http://localhost:8006/docs
- **Gateway Service**: http://localhost:8007/docs
- **Presence Service**: http://localhost:8008/docs

- **Keycloak**: http://localhost:8080 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

---

## Docker Compose Deployment

### Production-like Environment with Docker Compose

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale specific service
docker-compose up -d --scale messaging-service=3

# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

### Health Checks

```bash
# Check service health
curl http://localhost:8001/health
curl http://localhost:8002/health

# View service status
docker-compose ps
```

---

## Kubernetes Deployment

### Development Environment

```bash
# Apply development configuration
kubectl apply -k infra/k8s/overlays/dev

# Check deployment status
kubectl get pods -n colink-dev
kubectl get services -n colink-dev

# View logs
kubectl logs -f deployment/dev-users-service -n colink-dev

# Port forward for local access
kubectl port-forward -n colink-dev svc/dev-users-service 8001:8001
```

### Staging Environment

```bash
# Apply staging configuration
kubectl apply -k infra/k8s/overlays/staging

# Monitor rollout
kubectl rollout status deployment/staging-users-service -n colink-staging

# Check HPA status
kubectl get hpa -n colink-staging
```

### Production Environment

```bash
# Apply production configuration (⚠️ use with caution)
kubectl apply -k infra/k8s/overlays/production

# Monitor all deployments
kubectl get deployments -n colink -w

# Check pod health
kubectl get pods -n colink -o wide

# View events
kubectl get events -n colink --sort-by='.lastTimestamp'
```

### Update Image Tags

```bash
# Update to specific version
cd infra/k8s/overlays/production
kustomize edit set image \
  colink/users-service=ghcr.io/your-org/colink-users:v1.2.0

# Apply changes
kubectl apply -k .
```

---

## AWS EKS Production Setup

### 1. Create EKS Cluster

```bash
# Using eksctl
eksctl create cluster \
  --name colink-prod \
  --region us-east-1 \
  --version 1.28 \
  --nodegroup-name colink-workers \
  --node-type t3.xlarge \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 10 \
  --managed

# Update kubeconfig
aws eks update-kubeconfig --name colink-prod --region us-east-1
```

### 2. Install NGINX Ingress Controller

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer \
  --set controller.metrics.enabled=true
```

### 3. Install Cert-Manager (for TLS)

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@colink.io
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### 4. Create Kubernetes Secrets

```bash
# Database credentials
kubectl create secret generic colink-secrets \
  --from-literal=POSTGRES_PASSWORD='your-postgres-password' \
  --from-literal=MONGODB_PASSWORD='your-mongo-password' \
  --from-literal=REDIS_PASSWORD='your-redis-password' \
  --from-literal=AWS_ACCESS_KEY_ID='your-aws-key' \
  --from-literal=AWS_SECRET_ACCESS_KEY='your-aws-secret' \
  --from-literal=JWT_SECRET_KEY='your-jwt-secret-min-32-chars' \
  -n colink
```

### 5. Set Up External Databases (Recommended for Production)

**RDS PostgreSQL:**
```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier colink-prod-db \
  --db-instance-class db.r6g.xlarge \
  --engine postgres \
  --engine-version 15.4 \
  --master-username colink \
  --master-user-password 'your-password' \
  --allocated-storage 100 \
  --storage-type gp3 \
  --storage-encrypted \
  --backup-retention-period 7 \
  --multi-az
```

**DocumentDB (MongoDB-compatible):**
```bash
aws docdb create-db-cluster \
  --db-cluster-identifier colink-prod-docdb \
  --engine docdb \
  --master-username colink \
  --master-user-password 'your-password' \
  --backup-retention-period 7

aws docdb create-db-instance \
  --db-instance-identifier colink-prod-docdb-instance \
  --db-instance-class db.r6g.large \
  --engine docdb \
  --db-cluster-identifier colink-prod-docdb
```

**ElastiCache Redis:**
```bash
aws elasticache create-replication-group \
  --replication-group-id colink-prod-redis \
  --replication-group-description "CoLink Production Redis" \
  --engine redis \
  --cache-node-type cache.r6g.large \
  --num-cache-clusters 2 \
  --automatic-failover-enabled \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled
```

### 6. Deploy Application

```bash
# Update ConfigMap with external database URLs
kubectl edit configmap colink-config -n colink

# Deploy application
kubectl apply -k infra/k8s/overlays/production

# Monitor deployment
kubectl get pods -n colink -w
```

### 7. Configure DNS

```bash
# Get LoadBalancer DNS name
kubectl get svc ingress-nginx-controller -n ingress-nginx

# Create Route53 records pointing to LoadBalancer
# api.colink.io -> LoadBalancer DNS
# app.colink.io -> LoadBalancer DNS
```

---

## Environment Configuration

### Environment Variables

Key environment variables for each service:

```bash
# Database
POSTGRES_URL=postgresql://user:pass@host:5432/dbname
MONGODB_URL=mongodb://user:pass@host:27017/dbname
REDIS_URL=redis://:password@host:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Authentication
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_REALM=colink
KEYCLOAK_CLIENT_ID=colink-api
KEYCLOAK_CLIENT_SECRET=secret

# Storage
AWS_S3_BUCKET=colink-files
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# Security
JWT_SECRET_KEY=min-32-character-secret-key
SECRET_KEY=another-secret-key

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
PROMETHEUS_ENABLED=true
```

### ConfigMap Updates

```bash
# Edit ConfigMap
kubectl edit configmap colink-config -n colink

# Or apply from file
kubectl apply -f infra/k8s/base/configmap.yaml
```

### Secrets Management

**Production Best Practices:**

1. **AWS Secrets Manager:**
```bash
# Store secret
aws secretsmanager create-secret \
  --name colink/prod/postgres-password \
  --secret-string "your-password"

# Use External Secrets Operator in K8s
kubectl apply -f external-secrets-operator.yaml
```

2. **HashiCorp Vault:**
```bash
# Store in Vault
vault kv put secret/colink/prod/db password="your-password"
```

---

## Database Migrations

### PostgreSQL (Alembic)

```bash
# Create new migration
cd services/common/database
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Check current version
alembic current
```

### MongoDB Indexes

```bash
# Create indexes
python scripts/create_mongo_indexes.py

# Verify indexes
mongosh --eval "db.files.getIndexes()"
```

### Production Migration Strategy

1. **Backup databases before migration**
```bash
# PostgreSQL
pg_dump -h localhost -U colink colink > backup-$(date +%Y%m%d).sql

# MongoDB
mongodump --uri="mongodb://user:pass@host:27017/colink" --out=backup-$(date +%Y%m%d)
```

2. **Run migrations in staging first**
3. **Apply to production during maintenance window**
4. **Monitor for errors**
5. **Have rollback plan ready**

---

## Monitoring & Observability

### Prometheus Metrics

Access Prometheus:
```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```

Key metrics to monitor:
- Request rate: `rate(http_requests_total[5m])`
- Error rate: `rate(http_requests_total{status=~"5.."}[5m])`
- Latency: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- Pod CPU: `container_cpu_usage_seconds_total`
- Pod Memory: `container_memory_usage_bytes`

### Grafana Dashboards

Import dashboards:
```bash
kubectl port-forward -n monitoring svc/grafana 3000:3000
```

Dashboard IDs to import:
- **Kubernetes Cluster**: 7249
- **NGINX Ingress**: 9614
- **PostgreSQL**: 9628
- **Redis**: 11835
- **Kafka**: 7589

### Logging

**Using Loki:**
```bash
# Install Loki stack
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set promtail.enabled=true \
  --set grafana.enabled=true

# View logs in Grafana
# LogQL query: {app="users-service"}
```

### Tracing

**OpenTelemetry:**
```bash
# Deploy OTel Collector
kubectl apply -f otel-collector.yaml

# Services automatically export traces
# View in Jaeger or Zipkin
```

---

## Troubleshooting

### Common Issues

#### 1. Pod Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n colink

# Check logs
kubectl logs <pod-name> -n colink

# Check events
kubectl get events -n colink --field-selector involvedObject.name=<pod-name>
```

#### 2. Service Not Accessible

```bash
# Check service
kubectl get svc -n colink

# Check endpoints
kubectl get endpoints <service-name> -n colink

# Test from within cluster
kubectl run curl-test --image=curlimages/curl --rm -i --restart=Never -- \
  curl http://<service-name>:8001/health
```

#### 3. Database Connection Issues

```bash
# Test PostgreSQL connection
kubectl run psql-test --image=postgres:15 --rm -i --restart=Never -- \
  psql postgresql://user:pass@postgres:5432/colink -c "SELECT 1"

# Test MongoDB connection
kubectl run mongo-test --image=mongo:6 --rm -i --restart=Never -- \
  mongo mongodb://user:pass@mongodb:27017/colink --eval "db.adminCommand('ping')"
```

#### 4. High Memory/CPU Usage

```bash
# Check resource usage
kubectl top pods -n colink

# Adjust HPA settings
kubectl edit hpa <service>-hpa -n colink

# Increase resource limits
kubectl edit deployment <service> -n colink
```

#### 5. Image Pull Errors

```bash
# Check image pull secret
kubectl get secret -n colink

# Create image pull secret
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=<username> \
  --docker-password=<token> \
  -n colink

# Add to deployment
kubectl patch serviceaccount default -n colink \
  -p '{"imagePullSecrets": [{"name": "ghcr-secret"}]}'
```

### Debug Mode

Enable debug logging:
```bash
kubectl set env deployment/users-service DEBUG=true LOG_LEVEL=DEBUG -n colink
```

### Emergency Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/<service> -n colink

# Rollback to specific revision
kubectl rollout undo deployment/<service> --to-revision=2 -n colink

# Check rollout history
kubectl rollout history deployment/<service> -n colink
```

---

## Security Checklist

- [ ] All secrets stored in Secrets Manager/Vault
- [ ] TLS enabled on ingress
- [ ] Network policies configured
- [ ] RBAC properly set up
- [ ] Pod security policies applied
- [ ] Image scanning enabled
- [ ] No hardcoded credentials
- [ ] Database encryption at rest
- [ ] Backup strategy implemented
- [ ] Monitoring and alerting configured

---

## Maintenance

### Regular Tasks

**Daily:**
- Monitor error rates
- Check pod health
- Review resource usage

**Weekly:**
- Review logs for anomalies
- Check backup success
- Update dependencies (security patches)

**Monthly:**
- Review and optimize HPA settings
- Analyze cost and resource usage
- Update documentation
- Test disaster recovery

### Scaling

**Horizontal Pod Autoscaling:**
```bash
# Already configured via HPA manifests
kubectl get hpa -n colink
```

**Cluster Autoscaling:**
```bash
# EKS cluster autoscaler
eksctl create addon --name cluster-autoscaler --cluster colink-prod
```

---

## Support

For issues and questions:
- **GitHub Issues**: https://github.com/your-org/colink/issues
- **Documentation**: https://docs.colink.io
- **Slack**: #colink-support

---

**Last Updated**: November 2025
**Version**: 1.0.0
