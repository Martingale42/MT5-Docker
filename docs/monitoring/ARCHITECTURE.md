# Monitoring Architecture

Technical documentation for maintainers. Covers design decisions, data flow, and operational procedures.

## Design Rationale

### Why VictoriaMetrics over Prometheus?

We chose **VictoriaMetrics** (方案A) over the classic Prometheus stack for resource efficiency:

| Aspect | Prometheus | VictoriaMetrics |
|--------|------------|-----------------|
| RAM usage | 200-500MB | 50-100MB |
| Storage efficiency | ~2.1 bytes/sample | ~0.3 bytes/sample (7x better) |
| Query compatibility | Native PromQL | PromQL + MetricsQL superset |
| Long-term storage | Requires Thanos/Cortex | Built-in |

**Constraint**: MT5-Docker runs on 4 CPU / 2GB RAM. The monitoring stack must leave sufficient resources for MT5 itself.

### Why VictoriaLogs over Loki?

| Aspect | Grafana Loki | VictoriaLogs |
|--------|--------------|--------------|
| RAM usage | 200-500MB | 50-200MB |
| High cardinality | Poor (label explosion) | Good (auto-indexed) |
| Query speed | Slow on regex | 10-1000x faster |
| Maturity | Stable | Newer (GA late 2024) |

**Trade-off**: VictoriaLogs is newer with less community resources, but its efficiency is critical for our resource constraints.

### Why Vector over Promtail/Fluent Bit?

- **Promtail**: Loki-specific, not optimal for VictoriaLogs
- **Fluent Bit**: Good but less flexible transformation
- **Vector**: High-performance, supports Loki protocol (which VictoriaLogs accepts)

## Data Flow

### Metrics Pipeline

```
┌─────────────┐     scrape      ┌─────────┐    remote_write    ┌──────────────────┐
│ cAdvisor    │◄────────────────│ vmagent │──────────────────►│ VictoriaMetrics  │
│ (containers)│     :8080       │         │                    │ (TSDB)           │
└─────────────┘                 │  :8429  │                    │ :8428            │
                                │         │                    └────────┬─────────┘
┌─────────────┐     scrape      │         │                             │
│node_exporter│◄────────────────│         │                             │ query
│ (host)      │     :9100       └─────────┘                             ▼
└─────────────┘                                                 ┌───────────────┐
                                                                │   Grafana     │
                                                                │   :3000       │
                                                                └───────────────┘
```

**Flow**:
1. **cAdvisor** exposes container metrics at `:8080/metrics`
2. **node_exporter** exposes host metrics at `:9100/metrics`
3. **vmagent** scrapes both every 15s (configured in `prometheus.yml`)
4. **vmagent** forwards to **VictoriaMetrics** via `remote_write`
5. **Grafana** queries VictoriaMetrics using standard Prometheus API

### Logs Pipeline

```
┌─────────────┐                 ┌─────────┐     Loki API       ┌──────────────────┐
│ Docker      │  docker.sock   │ Vector  │   /insert/loki     │ VictoriaLogs     │
│ containers  │───────────────►│         │──────────────────►│                  │
│             │                 │         │                    │ :9428            │
└─────────────┘                 └─────────┘                    └────────┬─────────┘
                                                                        │
                                                                        │ query
                                                                        ▼
                                                               ┌────────────────┐
                                                               │ VictoriaLogs   │
                                                               │ vmui           │
                                                               └────────────────┘
```

**Flow**:
1. **Vector** connects to Docker socket to stream container logs
2. **Vector** transforms logs (adds service label, parses JSON)
3. **Vector** sends to **VictoriaLogs** using Loki-compatible API
4. Query via **vmui** at `:9428/select/vmui`

**Note**: We use Vector's `loki` sink because VictoriaLogs supports the Loki push protocol. The `http` sink with `jsonline` encoding had compatibility issues (sent arrays instead of newline-delimited JSON).

## Configuration Files

### monitoring/vmagent/prometheus.yml

Defines scrape targets for metrics collection:

```yaml
scrape_configs:
  - job_name: 'cadvisor'      # Container metrics
  - job_name: 'node-exporter' # Host metrics
  - job_name: 'victoriametrics' # Self-monitoring
  - job_name: 'grafana'       # Grafana metrics
```

**Customization points**:
- `scrape_interval`: Default 15s, increase for lower overhead
- `metric_relabel_configs`: Filter metrics to reduce cardinality

### monitoring/vector/vector.toml

Defines log collection and routing:

```toml
[sources.docker_logs]
include_containers = ["mt5zmq", "grafana", ...]  # Which containers

[sinks.victorialogs]
type = "loki"                    # Use Loki protocol
endpoint = "http://victorialogs:9428/insert"
```

**Customization points**:
- `include_containers`: Add/remove containers to monitor
- `[sinks.victorialogs.labels]`: Add custom labels for filtering

### monitoring/grafana/provisioning/datasources/datasources.yml

Pre-configures Grafana data sources:

```yaml
datasources:
  - name: VictoriaMetrics
    type: prometheus           # VictoriaMetrics is Prometheus-compatible
    url: http://victoriametrics:8428
```

## Network Architecture

All services communicate via the `monitoring` Docker network:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        monitoring network                            │
│                                                                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ mt5zmq  │  │ grafana │  │victoria │  │victoria │  │ vmagent │   │
│  │         │  │  :3000  │  │ metrics │  │  logs   │  │  :8429  │   │
│  │         │  │         │  │  :8428  │  │  :9428  │  │         │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
│                                                                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                              │
│  │cadvisor │  │  node   │  │ vector  │                              │
│  │  :8080  │  │exporter │  │         │                              │
│  │         │  │  :9100  │  │         │                              │
│  └─────────┘  └─────────┘  └─────────┘                              │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    Host ports (127.0.0.1 only)
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
          :3000           :8428           :9428
         Grafana      VictoriaMetrics  VictoriaLogs
```

**Security**: All monitoring ports bind to `127.0.0.1` only - not exposed externally.

## Operational Procedures

### Adding a New Scrape Target

1. Expose metrics endpoint in your service
2. Add to `monitoring/vmagent/prometheus.yml`:
   ```yaml
   - job_name: 'my-service'
     static_configs:
       - targets: ['my-service:9090']
   ```
3. Restart vmagent: `docker compose restart vmagent`
4. Verify: `curl http://localhost:8429/targets`

### Adding Container Logs

1. Edit `monitoring/vector/vector.toml`:
   ```toml
   [sources.docker_logs]
   include_containers = ["mt5zmq", "grafana", "my-new-service"]
   ```
2. Restart Vector: `docker compose restart vector`

### Changing Retention Period

**Metrics** (VictoriaMetrics):
```yaml
# docker-compose.yml
victoriametrics:
  command:
    - '--retentionPeriod=90d'  # Change from 30d to 90d
```

**Logs** (VictoriaLogs):
```yaml
# docker-compose.yml
victorialogs:
  command:
    - '--retentionPeriod=14d'  # Change from 7d to 14d
```

### Backup and Restore

**Backup volumes**:
```bash
# Stop services first
docker compose stop victoriametrics victorialogs grafana

# Backup
docker run --rm -v mt5-docker_vmdata:/data -v $(pwd):/backup alpine \
  tar czf /backup/vmdata-backup.tar.gz /data

docker run --rm -v mt5-docker_vldata:/data -v $(pwd):/backup alpine \
  tar czf /backup/vldata-backup.tar.gz /data

docker run --rm -v mt5-docker_grafana-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/grafana-backup.tar.gz /data

# Restart
docker compose start victoriametrics victorialogs grafana
```

**Restore**:
```bash
docker compose down
docker volume rm mt5-docker_vmdata  # Remove existing

docker volume create mt5-docker_vmdata
docker run --rm -v mt5-docker_vmdata:/data -v $(pwd):/backup alpine \
  tar xzf /backup/vmdata-backup.tar.gz -C /

docker compose up -d
```

## Troubleshooting

### High Memory Usage

**Symptom**: VictoriaMetrics or VictoriaLogs using more RAM than expected

**Diagnosis**:
```bash
docker stats --no-stream
```

**Solutions**:
1. Reduce retention period
2. Add metric filters in vmagent to reduce cardinality
3. Increase memory limits if host has capacity

### Metrics Missing

**Symptom**: Grafana shows "No data"

**Checklist**:
1. Check vmagent targets: `curl http://localhost:8429/targets`
2. Check VictoriaMetrics is receiving: `curl "http://localhost:8428/api/v1/query?query=up"`
3. Check time range in Grafana (might be querying wrong period)

### Logs Not Appearing

**Symptom**: VictoriaLogs vmui shows no logs

**Checklist**:
1. Check Vector is running: `docker logs vector --tail 20`
2. Check ingestion: `curl http://localhost:9428/metrics | grep vl_rows_ingested`
3. Verify container is in `include_containers` list

### Grafana Can't Connect to Data Source

**Symptom**: "Bad Gateway" or connection errors

**Checklist**:
1. Verify service is running: `docker compose ps`
2. Check network connectivity: `docker exec grafana wget -q -O- http://victoriametrics:8428/health`
3. Verify data source URL uses container name, not localhost

## Performance Tuning

### Reduce Scrape Frequency

For lower-traffic environments, increase scrape interval:

```yaml
# monitoring/vmagent/prometheus.yml
global:
  scrape_interval: 30s  # Default is 15s
```

### Limit Collected Metrics

Add filters to reduce storage:

```yaml
# monitoring/vmagent/prometheus.yml
- job_name: 'cadvisor'
  metric_relabel_configs:
    - source_labels: [__name__]
      regex: 'container_(cpu|memory|network)_.*'
      action: keep  # Only keep CPU, memory, network metrics
```

### Reduce Log Verbosity

Exclude noisy containers:

```toml
# monitoring/vector/vector.toml
[sources.docker_logs]
exclude_containers = ["cadvisor", "node-exporter"]  # These are noisy
```
