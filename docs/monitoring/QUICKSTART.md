# Monitoring Quickstart

Personal reference. Copy-paste commands.

## URLs

```
Grafana:          http://localhost:3000      (admin/admin)
VictoriaMetrics:  http://localhost:8428/vmui
VictoriaLogs:     http://localhost:9428/select/vmui
cAdvisor:         http://localhost:8080
```

## Common Tasks

### Start/Stop

```bash
# Start all
docker compose up -d

# Stop all
docker compose down

# Restart monitoring only (keep MT5 running)
docker compose restart victoriametrics victorialogs grafana vmagent vector

# View status
docker compose ps
```

### Check Logs

```bash
# MT5 logs (last 100 lines)
docker logs mt5zmq --tail 100

# Grafana logs
docker logs grafana --tail 50

# Vector (log collector) logs
docker logs vector --tail 50

# All container logs (follow)
docker compose logs -f
```

### Query Metrics (curl)

```bash
# Check all targets are up
curl -s "http://localhost:8428/api/v1/query?query=up"

# MT5 container CPU usage (last 5min)
curl -s 'http://localhost:8428/api/v1/query?query=rate(container_cpu_usage_seconds_total{name="mt5zmq"}[5m])'

# MT5 container memory
curl -s 'http://localhost:8428/api/v1/query?query=container_memory_usage_bytes{name="mt5zmq"}'

# Host memory available
curl -s 'http://localhost:8428/api/v1/query?query=node_memory_MemAvailable_bytes'
```

### Query Logs (curl)

```bash
# All logs (last 10)
curl -s "http://localhost:9428/select/logsql/query?query=*&limit=10"

# MT5 logs only
curl -s "http://localhost:9428/select/logsql/query?query=service:mt5zmq&limit=20"

# Logs containing "error"
curl -s "http://localhost:9428/select/logsql/query?query=error&limit=20"

# Grafana logs
curl -s "http://localhost:9428/select/logsql/query?query=service:grafana&limit=20"
```

### Import Grafana Dashboard

1. Open http://localhost:3000
2. Click **+** → **Import**
3. Enter dashboard ID:
   - `14282` - Docker/cAdvisor monitoring
   - `1860` - Node Exporter Full
4. Select "VictoriaMetrics" as data source
5. Click **Import**

### Reset/Cleanup

```bash
# Delete all monitoring data (keeps MT5 data)
docker compose down
docker volume rm mt5-docker_vmdata mt5-docker_vldata mt5-docker_grafana-data mt5-docker_vmagent-data
docker compose up -d

# Full reset (including MT5 config)
docker compose down -v
docker compose up -d
```

## Troubleshooting

### No metrics in Grafana

```bash
# Check vmagent is scraping
curl -s http://localhost:8429/targets

# Check VictoriaMetrics has data
curl -s "http://localhost:8428/api/v1/query?query=up"
```

### No logs in VictoriaLogs

```bash
# Check Vector is running
docker logs vector --tail 20

# Check ingestion count
curl -s http://localhost:9428/metrics | grep vl_rows_ingested
```

### Service won't start

```bash
# Check specific service logs
docker compose logs <service-name>

# Recreate specific service
docker compose up -d --force-recreate <service-name>
```

## Useful PromQL Queries

```promql
# Container CPU % (of limit)
rate(container_cpu_usage_seconds_total{name="mt5zmq"}[5m]) * 100

# Container memory % (of limit)
container_memory_usage_bytes{name="mt5zmq"} / container_spec_memory_limit_bytes{name="mt5zmq"} * 100

# Network received (bytes/sec)
rate(container_network_receive_bytes_total{name="mt5zmq"}[5m])

# Disk read (bytes/sec)
rate(container_fs_reads_bytes_total{name="mt5zmq"}[5m])
```

## Useful LogsQL Queries

```logsql
# All logs from MT5
service:mt5zmq

# Errors only
error OR ERROR OR Error

# MT5 errors
service:mt5zmq AND error

# Last hour
_time:1h

# Specific time range
_time:[2024-01-19T10:00:00Z, 2024-01-19T11:00:00Z]
```
