# Grafana Dashboards Tutorial

Learn to visualize MT5-Docker metrics with Grafana dashboards.

## Prerequisites

- Monitoring stack running (`docker compose up -d`)
- Access to http://localhost:3000 (Grafana)
- Default login: `admin` / `admin`

## Understanding Grafana

### Core Concepts

**Dashboard**: A collection of panels arranged on a canvas. Think of it as a "page" of visualizations.

**Panel**: A single visualization (graph, gauge, table, etc.) showing specific data.

**Data Source**: Where Grafana gets data from. We use VictoriaMetrics (configured as "VictoriaMetrics" in the datasource list).

**Query**: The PromQL expression that fetches data for a panel.

**Variables**: Dynamic values that let you filter dashboards (e.g., select which container to view).

### Panel Types

| Type | Best For |
|------|----------|
| **Time series** | Values changing over time (CPU, memory) |
| **Stat** | Single current value with optional sparkline |
| **Gauge** | Percentage or bounded values |
| **Table** | Listing multiple items |
| **Bar gauge** | Comparing multiple values |

## Importing Pre-Built Dashboards

The fastest way to get started is importing community dashboards.

### Step 1: Import cAdvisor Dashboard

1. Click **+** (plus icon) in left sidebar
2. Select **Import**
3. Enter ID: `14282`
4. Click **Load**
5. Select "VictoriaMetrics" as the data source
6. Click **Import**

You now have a full Docker monitoring dashboard showing:
- Container CPU usage
- Container memory usage
- Network I/O
- Disk I/O

### Step 2: Import Node Exporter Dashboard

1. Click **+** → **Import**
2. Enter ID: `1860`
3. Select "VictoriaMetrics" as data source
4. Click **Import**

This shows host-level metrics:
- System load
- Memory usage
- Disk space
- Network traffic

### Recommended Dashboard IDs

| ID | Name | Shows |
|----|------|-------|
| 14282 | cAdvisor Exporter | Container metrics |
| 1860 | Node Exporter Full | Host system metrics |
| 11074 | Node Exporter (simpler) | Host metrics (simplified) |
| 12831 | Docker Container | Container overview |

## Creating a Custom Dashboard

Let's build a simple MT5-focused dashboard from scratch.

### Step 1: Create New Dashboard

1. Click **+** → **New Dashboard**
2. Click **Add visualization**

### Step 2: Add MT5 Memory Panel

1. Select "VictoriaMetrics" as data source
2. In the query box, enter:
   ```promql
   container_memory_usage_bytes{name="mt5zmq"}
   ```
3. On the right panel:
   - Title: "MT5 Memory Usage"
   - Unit: Select **Data → bytes(IEC)** (will show as MB/GB)
4. Click **Apply**

### Step 3: Add MT5 CPU Panel

1. Click **Add** → **Visualization**
2. Query:
   ```promql
   rate(container_cpu_usage_seconds_total{name="mt5zmq"}[5m]) * 100
   ```
3. Settings:
   - Title: "MT5 CPU Usage"
   - Unit: **Misc → Percent (0-100)**
4. Click **Apply**

### Step 4: Add Memory Percentage Gauge

1. Add visualization
2. Change visualization type to **Gauge** (top-right dropdown)
3. Query:
   ```promql
   container_memory_usage_bytes{name="mt5zmq"}
   /
   container_spec_memory_limit_bytes{name="mt5zmq"}
   * 100
   ```
4. Settings:
   - Title: "MT5 Memory %"
   - Unit: **Misc → Percent (0-100)**
   - Under "Standard options" → Max: 100
   - Under "Thresholds":
     - Green: 0
     - Yellow: 70
     - Red: 90
5. Click **Apply**

### Step 5: Save Dashboard

1. Click the **Save** icon (top right)
2. Name: "MT5 Overview"
3. Click **Save**

## Useful Queries for MT5

### Container Metrics

```promql
# Memory usage in bytes
container_memory_usage_bytes{name="mt5zmq"}

# Memory as percentage of limit
container_memory_usage_bytes{name="mt5zmq"} / container_spec_memory_limit_bytes{name="mt5zmq"} * 100

# CPU usage (cores)
rate(container_cpu_usage_seconds_total{name="mt5zmq"}[5m])

# CPU as percentage of limit (4 cores = 400%)
rate(container_cpu_usage_seconds_total{name="mt5zmq"}[5m]) / 4 * 100

# Network received (bytes/sec)
rate(container_network_receive_bytes_total{name="mt5zmq"}[5m])

# Network sent (bytes/sec)
rate(container_network_transmit_bytes_total{name="mt5zmq"}[5m])
```

### Host Metrics

```promql
# Host CPU usage percentage
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Host memory usage percentage
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# Disk usage percentage (root filesystem)
100 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} * 100)

# Host uptime
node_time_seconds - node_boot_time_seconds
```

### All Containers Comparison

```promql
# Memory usage for all containers
container_memory_usage_bytes{name!=""}

# CPU for all containers
rate(container_cpu_usage_seconds_total{name!=""}[5m])
```

## Using Variables

Variables make dashboards dynamic. Let's add a container selector.

### Step 1: Add Variable

1. Go to Dashboard Settings (gear icon)
2. Click **Variables** → **Add variable**
3. Configure:
   - Name: `container`
   - Type: Query
   - Data source: VictoriaMetrics
   - Query: `label_values(container_memory_usage_bytes, name)`
   - Multi-value: Enable
   - Include All option: Enable
4. Click **Apply**

### Step 2: Use Variable in Queries

Update your panel queries to use the variable:

```promql
container_memory_usage_bytes{name=~"$container"}
```

The `=~` means regex match, and `$container` will be replaced with selected value(s).

Now you can select which container(s) to view from a dropdown at the top of the dashboard.

## Setting Up Alerts

Grafana can alert you when metrics cross thresholds.

### Step 1: Create Alert Rule

1. Go to **Alerting** → **Alert rules**
2. Click **New alert rule**
3. Configure:
   - Name: "MT5 High Memory"
   - Query:
     ```promql
     container_memory_usage_bytes{name="mt5zmq"} / container_spec_memory_limit_bytes{name="mt5zmq"} * 100
     ```
   - Condition: IS ABOVE 90
   - Evaluate every: 1m
   - For: 5m (alert after 5 minutes above threshold)
4. Add labels and annotations as needed
5. Click **Save and exit**

### Common Alert Conditions

| Alert | Query | Threshold |
|-------|-------|-----------|
| High Memory | `container_memory_usage_bytes{name="mt5zmq"} / container_spec_memory_limit_bytes{name="mt5zmq"} * 100` | > 90% |
| High CPU | `rate(container_cpu_usage_seconds_total{name="mt5zmq"}[5m])` | > 3.5 (87.5% of 4 cores) |
| Container Down | `up{job="cadvisor"}` | == 0 |
| Low Disk | `node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} * 100` | < 10% |

## Tips and Best Practices

### Panel Organization

- Group related panels together
- Use rows to organize sections (click "Add" → "Row")
- Put most important metrics at the top

### Time Range

- Use relative time (Last 1 hour, Last 24 hours) for operational dashboards
- The time picker is in the top-right corner

### Refresh Rate

- Set auto-refresh for real-time monitoring
- Click the refresh dropdown (top-right) → Select interval (e.g., 10s)

### Sharing

- **Snapshot**: Point-in-time copy (Sharing → Snapshot)
- **Link**: Share current view with time range (Sharing → Link)
- **Export**: Download JSON (Dashboard settings → JSON Model)

## Next Steps

- [03_QUERYING_LOGS.md](./03_QUERYING_LOGS.md) - Learn to search and analyze logs
- Explore more dashboards at https://grafana.com/grafana/dashboards/
