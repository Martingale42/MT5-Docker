# Getting Started with MT5-Docker Monitoring

This tutorial introduces the monitoring stack and helps you understand what's happening under the hood.

## What is Observability?

Observability is the ability to understand what's happening inside your system by examining its outputs. For MT5-Docker, this means:

- **Metrics**: Numerical measurements over time (CPU usage, memory, request counts)
- **Logs**: Timestamped text records of events (errors, warnings, status messages)

Together, they help you answer questions like:
- "Why did MT5 crash last night?"
- "Is the system under memory pressure?"
- "What was happening when that trade failed?"

## The Stack Components

### Metrics Side

```
Your Containers ──► cAdvisor ──► vmagent ──► VictoriaMetrics ──► Grafana
     │                                              │
     └──► node_exporter ─────────────────────────────┘
                (host metrics)
```

**cAdvisor** (Container Advisor): A Google tool that watches Docker containers and exposes metrics like CPU, memory, network, and disk usage.

**node_exporter**: Exposes host-level metrics - the actual machine's CPU, memory, disk, and network.

**vmagent**: A lightweight agent that periodically "scrapes" (fetches) metrics from cAdvisor and node_exporter, then forwards them.

**VictoriaMetrics**: A time-series database that stores metrics efficiently. Think of it as a specialized database optimized for "value at timestamp" data.

**Grafana**: A visualization platform that queries VictoriaMetrics and displays beautiful dashboards.

### Logs Side

```
Your Containers ──► Vector ──► VictoriaLogs ──► vmui (web interface)
```

**Vector**: Connects to Docker and streams container logs in real-time. It adds metadata (container name, timestamp) and forwards to storage.

**VictoriaLogs**: A log database optimized for fast searching. Unlike traditional databases, it's designed for append-only log data.

## Understanding Metrics

### What is a Metric?

A metric is a named measurement with a value and timestamp:

```
container_memory_usage_bytes{name="mt5zmq"} 524288000 1705678800
│                           │                │          │
│                           │                │          └─ timestamp
│                           │                └─ value (500MB)
│                           └─ labels (which container)
└─ metric name
```

### Labels

Labels are key-value pairs that add dimensions to metrics. They let you filter and group data:

```
container_cpu_usage_seconds_total{name="mt5zmq", cpu="cpu00"}
container_cpu_usage_seconds_total{name="mt5zmq", cpu="cpu01"}
container_cpu_usage_seconds_total{name="grafana", cpu="cpu00"}
```

You can query:
- All CPUs for mt5zmq: `{name="mt5zmq"}`
- CPU 00 for all containers: `{cpu="cpu00"}`

### PromQL Basics

PromQL (Prometheus Query Language) is how you query metrics. VictoriaMetrics supports it fully.

**Instant query** - current value:
```promql
container_memory_usage_bytes{name="mt5zmq"}
```

**Range query** - values over time:
```promql
container_memory_usage_bytes{name="mt5zmq"}[5m]
```

**Rate** - per-second change (essential for counters):
```promql
rate(container_cpu_usage_seconds_total{name="mt5zmq"}[5m])
```

## Understanding Logs

### Log Structure in VictoriaLogs

Each log entry has:
- `_time`: When the log was generated
- `_msg`: The actual log message
- `_stream`: Labels identifying the source (e.g., `{service="mt5zmq"}`)

Example:
```json
{
  "_time": "2024-01-19T10:30:45Z",
  "_msg": "[WATCHDOG] MT5 is running (CPU: 0.1%)",
  "_stream": "{container=\"mt5zmq\",service=\"mt5zmq\"}",
  "service": "mt5zmq"
}
```

### LogsQL Basics

LogsQL is VictoriaLogs' query language.

**Simple search**:
```logsql
error
```

**Filter by label**:
```logsql
service:mt5zmq
```

**Combine conditions**:
```logsql
service:mt5zmq AND error
```

**Time range**:
```logsql
_time:1h    # last hour
```

## Hands-On: Your First Queries

### Step 1: Check the System is Running

```bash
docker compose ps
```

All services should show "Up" status.

### Step 2: Query Metrics via CLI

Check that metrics are being collected:

```bash
curl -s "http://localhost:8428/api/v1/query?query=up" | python3 -m json.tool
```

You should see multiple results with `"value": [..., "1"]` indicating targets are up.

### Step 3: Query Metrics via Web UI

1. Open http://localhost:8428/vmui
2. In the query box, enter: `container_memory_usage_bytes`
3. Click "Execute Query"
4. Switch to "Graph" tab to see memory over time

### Step 4: Query Logs via CLI

```bash
curl -s "http://localhost:9428/select/logsql/query?query=*&limit=5"
```

### Step 5: Query Logs via Web UI

1. Open http://localhost:9428/select/vmui
2. Enter `*` in the query box
3. Click "Execute Query"
4. Try filtering: `service:mt5zmq`

### Step 6: Open Grafana

1. Open http://localhost:3000
2. Login with `admin` / `admin`
3. Go to Dashboards → Browse
4. If empty, import a dashboard (see next tutorial)

## Key Concepts Recap

| Concept | What it is | Example |
|---------|------------|---------|
| **Metric** | Numerical measurement | CPU usage: 45% |
| **Label** | Dimension/filter for metrics | `name="mt5zmq"` |
| **Time series** | Metric + labels + values over time | Memory usage graph |
| **Log** | Text event with timestamp | "MT5 started successfully" |
| **Scraping** | Periodically fetching metrics | Every 15 seconds |
| **Retention** | How long data is kept | 30 days for metrics |

## Next Steps

- [02_GRAFANA_DASHBOARDS.md](./02_GRAFANA_DASHBOARDS.md) - Create visualizations
- [03_QUERYING_LOGS.md](./03_QUERYING_LOGS.md) - Advanced log queries
