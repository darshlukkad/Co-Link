# CoLink Monitoring & Observability

This directory contains monitoring and observability configuration for the CoLink platform.

## Contents

- **prometheus.yml** - Prometheus configuration with scrape targets
- **prometheus-rules.yml** - Alerting rules for Prometheus
- **grafana-dashboards/** - Pre-built Grafana dashboard definitions

## Quick Start

### Prometheus

```bash
# Deploy Prometheus using Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values prometheus-values.yaml
```

### Grafana

```bash
# Access Grafana (default credentials: admin/prom-operator)
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Import dashboards
# Navigate to: Dashboards -> Import
# Upload JSON files from grafana-dashboards/
```

### Custom Metrics

Add to your service code:

```python
from prometheus_client import Counter, Histogram, Gauge

# Request counter
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Request duration
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Active connections
websocket_active_connections = Gauge(
    'websocket_active_connections',
    'Active WebSocket connections'
)
```

## Available Dashboards

1. **CoLink Services Overview** - High-level view of all microservices
2. **API Performance** - Request rates, latencies, error rates
3. **Database Monitoring** - PostgreSQL, MongoDB, Redis metrics
4. **Kafka Monitoring** - Topic metrics, consumer lag
5. **Business Metrics** - Messages, files, users, searches

## Alerting

Alerts are defined in `prometheus-rules.yml` and include:

- Service health (up/down status)
- High error rates (> 5%)
- High latency (P95 > 1s)
- Resource usage (CPU > 80%, Memory > 90%)
- Database connection pool exhaustion
- Kafka consumer lag
- WebSocket connection issues
- SLA breaches

## Alert Routing

Configure Alertmanager for notifications:

```yaml
# alertmanager.yml
global:
  slack_api_url: 'YOUR_SLACK_WEBHOOK'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
    - match:
        severity: warning
      receiver: 'slack'

receivers:
  - name: 'default'
    email_configs:
      - to: 'ops@colink.io'
  - name: 'slack'
    slack_configs:
      - channel: '#alerts'
        title: 'CoLink Alert'
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_KEY'
```

## Metrics Endpoints

All services expose metrics at `/metrics`:

- http://users-service:8001/metrics
- http://messaging-service:8002/metrics
- http://files-service:8003/metrics
- http://search-service:8004/metrics
- http://admin-service:8005/metrics
- http://channels-service:8006/metrics
- http://gateway-service:8007/metrics
- http://presence-service:8008/metrics

## Key Metrics

### HTTP Metrics
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency histogram
- `http_requests_in_progress` - Current in-flight requests

### Business Metrics
- `messages_sent_total` - Total messages sent
- `file_uploads_total` - Total file uploads
- `search_queries_total` - Total search queries
- `user_registrations_total` - Total user registrations

### Database Metrics
- `db_connections_active` - Active database connections
- `db_query_duration_seconds` - Query execution time
- `db_connection_errors_total` - Connection errors

### Cache Metrics
- `redis_hits_total` - Cache hits
- `redis_misses_total` - Cache misses
- `redis_memory_used_bytes` - Memory usage

### WebSocket Metrics
- `websocket_active_connections` - Active connections
- `websocket_messages_sent_total` - Messages sent
- `websocket_messages_received_total` - Messages received
- `websocket_disconnections_total` - Disconnection count

## Logging

Use Loki for log aggregation:

```bash
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set promtail.enabled=true \
  --set grafana.enabled=true
```

Query logs in Grafana:
```logql
{app="users-service"} |= "error"
{namespace="colink"} | json | level="ERROR"
```

## Tracing

OpenTelemetry configuration:

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

tracer_provider = TracerProvider()
tracer_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="otel-collector:4317"))
)
trace.set_tracer_provider(tracer_provider)
```

## SLIs and SLOs

### Service Level Indicators (SLIs)
- **Availability**: Percentage of successful requests (non-5xx)
- **Latency**: P95 request duration
- **Error Rate**: Percentage of 5xx responses

### Service Level Objectives (SLOs)
- **Availability**: 99.9% (3 nines)
- **Latency**: P95 < 500ms, P99 < 1s
- **Error Rate**: < 0.1%

### Error Budget
- Monthly error budget: 43.2 minutes of downtime
- Weekly error budget: 10.08 minutes of downtime

## Troubleshooting

### High Memory Usage
```promql
topk(5, container_memory_usage_bytes{namespace="colink"})
```

### Slow Queries
```promql
topk(10, rate(pg_stat_statements_mean_exec_time_seconds[5m]))
```

### High Error Rate
```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) by (job, status)
```

## Best Practices

1. **Use labels consistently** across all metrics
2. **Set appropriate retention** periods for time series data
3. **Create runbooks** for each alert
4. **Test alerting** rules in staging first
5. **Monitor the monitors** - ensure Prometheus itself is healthy
6. **Use recording rules** for frequently queried metrics
7. **Set up dashboards** before deploying to production
8. **Document SLIs and SLOs** for all services

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Google SRE Book - Monitoring](https://sre.google/sre-book/monitoring-distributed-systems/)
