# MT5-Docker Monitoring & Observability

This directory contains the monitoring and observability stack for MT5-Docker,
including Prometheus metrics, Grafana dashboards, and structured logging.

## Components

### 1. Prometheus Metrics Exporter
**File:** `prometheus_exporter.py`

Exposes MT5 JsonAPI metrics in Prometheus format for scraping.

**Metrics Exposed:**
- `zmq_requests_total` - Counter of ZMQ requests by action type
- `zmq_request_duration_seconds` - Histogram of request latencies
- `zmq_errors_total` - Counter of errors by action and error type
- `mt5_connection_status` - Gauge (1=connected, 0=disconnected)
- `mt5_account_balance` - Gauge of account balance in USD
- `mt5_account_equity` - Gauge of account equity
- `mt5_account_margin` - Gauge of margin used
- `mt5_account_margin_free` - Gauge of free margin
- `mt5_info` - Info metric with broker/server details

**Usage:**
```bash
# Start monitoring stack
docker-compose --profile monitoring up -d

# Or run standalone
python3 prometheus_exporter.py --port 9090 --mt5-host localhost --interval 30
```

### 2. Prometheus Server
**Directory:** `prometheus/`

Time-series database for storing and querying metrics.

**Configuration:**
- `prometheus.yml` - Main Prometheus configuration
- `alerts.yml` - Alert rules for automated monitoring

**Accessing Prometheus:**
- URL: http://localhost:9091
- Query examples:
  ```promql
  # Request rate
  rate(zmq_requests_total[5m])

  # P95 latency
  histogram_quantile(0.95, rate(zmq_request_duration_seconds_bucket[5m]))

  # Error rate
  rate(zmq_errors_total[5m])
  ```

### 3. Grafana Dashboards
**Directory:** `grafana/dashboards/`

Visualization dashboards for metrics.

**Accessing Grafana:**
- URL: http://localhost:3000
- Default credentials: `admin / admin`
- Dashboard: "MT5-Docker Monitoring Dashboard"

**Dashboard Panels:**
- Connection status gauge
- Account balance & equity over time
- Request rate by action type
- Request latency percentiles (p50, p95, p99)
- Error counts
- Margin status

### 4. Structured JSON Logging
**File:** `logging_config.py`

Provides consistent JSON-formatted logging for easy parsing.

**Usage in Code:**
```python
from monitoring.logging_config import get_logger

# Create logger
logger = get_logger(__name__)

# Log with context
logger.info("Processing trade", extra={
    "symbol": "EURUSD",
    "volume": 0.1,
    "action": "buy"
})

# Log with persistent context
logger_with_context = get_logger(__name__, context={
    "user_id": "12345",
    "session_id": "abcdef"
})
logger_with_context.info("User action")  # Context automatically included
```

**Log Format:**
```json
{
  "timestamp": "2025-01-13T10:30:45.123456Z",
  "level": "INFO",
  "logger": "zmq_client",
  "message": "Processing trade",
  "service": "mt5-docker",
  "environment": "production",
  "source": {
    "file": "zmq_client.py",
    "line": 42,
    "function": "send_command"
  },
  "symbol": "EURUSD",
  "volume": 0.1,
  "action": "buy"
}
```

## Quick Start

### Starting the Full Monitoring Stack

```bash
# Start MT5 + Monitoring stack
docker-compose up -d  # MT5 only
docker-compose --profile monitoring up -d  # Add monitoring

# Verify services
docker-compose --profile monitoring ps

# Check health
docker-compose --profile monitoring logs mt5-exporter
```

### Accessing Monitoring UIs

| Service | URL | Purpose |
|---------|-----|---------|
| Prometheus | http://localhost:9091 | Metrics database & queries |
| Grafana | http://localhost:3000 | Dashboards & visualization |
| Metrics Exporter | http://localhost:9090/metrics | Raw Prometheus metrics |

### Viewing Metrics

**Option 1: Grafana Dashboard (Recommended)**
1. Open http://localhost:3000
2. Login with `admin / admin`
3. Navigate to "MT5-Docker Monitoring Dashboard"
4. View real-time metrics and historical data

**Option 2: Prometheus Queries**
1. Open http://localhost:9091
2. Go to "Graph" tab
3. Enter PromQL query:
   ```promql
   # Current account balance
   mt5_account_balance

   # Request rate by action
   rate(zmq_requests_total[5m])

   # Error percentage
   rate(zmq_errors_total[5m]) / rate(zmq_requests_total[5m]) * 100
   ```

**Option 3: Raw Metrics**
```bash
curl http://localhost:9090/metrics
```

## Alert Rules

Alerting rules are defined in `prometheus/alerts.yml`:

### Critical Alerts
- **MT5ConnectionDown** - MT5 not responding for >2 minutes
- **LowMarginLevel** - Free margin <20% of equity
- **NegativeAccountBalance** - Account balance negative

### Warning Alerts
- **HighErrorRate** - Error rate >0.1 errors/sec for >5 minutes
- **HighRequestLatency** - P95 latency >2 seconds for >10 minutes
- **SignificantBalanceDrop** - Balance dropped >10% in 1 hour

### Info Alerts
- **UnusualRequestVolume** - Request rate >100 req/sec
- **MT5ExporterDown** - Metrics exporter not responding

## Customization

### Adding New Metrics

1. Edit `prometheus_exporter.py`:
```python
# Define metric
my_custom_metric = Gauge('my_metric_name', 'Description')

# Update in collection loop
def collect_custom_metrics(self):
    my_custom_metric.set(some_value)
```

2. Add to Grafana dashboard:
- Edit `grafana/dashboards/mt5-dashboard.json`
- Add new panel with PromQL query

### Adding New Alert Rules

Edit `prometheus/alerts.yml`:
```yaml
- alert: MyNewAlert
  expr: my_metric_name > threshold
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Alert title"
    description: "Alert description"
```

### Configuring Log Aggregation

**For ELK Stack (Elasticsearch/Logstash/Kibana):**
```bash
# Configure logging to file
python3 monitoring/prometheus_exporter.py --log-file /var/log/mt5/exporter.log

# Configure Logstash to read JSON logs
# Input: file { path => "/var/log/mt5/*.log" codec => json }
```

**For Grafana Loki:**
```yaml
# Add to docker-compose.yml
loki:
  image: grafana/loki:latest
  ports:
    - "3100:3100"
  volumes:
    - loki-data:/loki
```

## Troubleshooting

### Metrics Not Appearing

**Check Exporter Status:**
```bash
# View logs
docker-compose --profile monitoring logs mt5-exporter

# Check metrics endpoint
curl http://localhost:9090/metrics
```

**Check MT5 Connection:**
```bash
# Verify MT5 is running
docker-compose ps mt5zmq

# Check ZMQ ports
nc -zv localhost 2201
nc -zv localhost 2202
```

### Grafana Dashboard Not Loading

**Check Prometheus Data Source:**
1. Go to Grafana → Configuration → Data Sources
2. Add Prometheus data source: `http://prometheus:9090`
3. Test connection

**Import Dashboard:**
1. Go to Dashboards → Import
2. Upload `grafana/dashboards/mt5-dashboard.json`

### High Memory Usage

**Reduce Prometheus Retention:**
```yaml
# In docker-compose.yml
command:
  - '--storage.tsdb.retention.time=7d'  # Default: 15d
```

**Reduce Scrape Frequency:**
```yaml
# In prometheus.yml
scrape_interval: 60s  # Default: 15s
```

## Performance Considerations

- **Metrics Exporter**: Collects data every 30s by default (configurable via `--interval`)
- **Prometheus**: Scrapes every 15s, retains 15 days of data
- **Resource Usage**:
  - Exporter: ~50MB RAM
  - Prometheus: ~200-500MB RAM (depends on retention)
  - Grafana: ~100-200MB RAM

## Security

### Production Recommendations

1. **Change default passwords:**
```yaml
# In docker-compose.yml
environment:
  - GF_SECURITY_ADMIN_PASSWORD=strong_password_here
```

2. **Use authentication for Prometheus:**
```yaml
# Add to prometheus.yml
basic_auth_users:
  admin: $2b$12$hashed_password_here
```

3. **Enable HTTPS:**
- Use reverse proxy (nginx, traefik)
- Configure SSL certificates

4. **Network isolation:**
```yaml
# In docker-compose.yml
networks:
  monitoring:
    internal: true
```

## Further Reading

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)
