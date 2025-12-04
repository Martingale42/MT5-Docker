# Prometheus Monitoring Tutorial - From Zero to Hero

**Time to complete:** 90-120 minutes
**Prerequisites:** Docker basics, basic understanding of metrics

---

## Table of Contents

1. [Conceptual Understanding](#conceptual-understanding)
2. [How Prometheus Works](#how-prometheus-works)
3. [Hands-On Tutorial](#hands-on-tutorial)
4. [PromQL Query Language](#promql-query-language)
5. [Real Examples from MT5-Docker](#real-examples)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Conceptual Understanding

### What is Monitoring?

**Monitoring** is the practice of collecting, processing, and displaying information about the health and performance of your systems.

**Without monitoring:**
```
Your app is running... or is it?
  - Is it slow?
  - Are there errors?
  - Is it about to crash?
  - You have no idea until users complain!
```

**With monitoring:**
```
Dashboard shows:
  ✓ Request rate: 150 req/sec
  ✓ Error rate: 0.01%
  ✓ Latency p95: 45ms
  ✓ Memory usage: 450MB / 2GB
  ⚠️ Alert: Database connection pool 90% full!
```

### What is Prometheus?

**Prometheus** is an open-source monitoring system that:
- **Collects** metrics from your applications
- **Stores** them in a time-series database
- **Queries** metrics using PromQL
- **Alerts** when something goes wrong

**Think of it as:**
- A health monitor for your application
- A time machine for performance data
- An early warning system for problems

### Key Concepts

#### 1. Metrics
**Metrics** are numerical measurements over time.

**Examples:**
- `http_requests_total` = 15,234 (total requests)
- `request_duration_seconds` = 0.045 (response time)
- `memory_usage_bytes` = 450,000,000 (RAM used)

#### 2. Labels
**Labels** add dimensions to metrics.

**Example:**
```
http_requests_total{method="GET", endpoint="/api/users", status="200"} = 1000
http_requests_total{method="POST", endpoint="/api/users", status="201"} = 50
http_requests_total{method="GET", endpoint="/api/users", status="500"} = 2
```

Same metric, different labels = detailed insights!

#### 3. Metric Types

**Counter** - Only goes up (resets on restart)
```
Examples:
- Total requests
- Total errors
- Total bytes sent
```

**Gauge** - Can go up and down
```
Examples:
- Current CPU usage
- Current memory usage
- Number of active connections
```

**Histogram** - Tracks distribution of values
```
Examples:
- Request latency buckets
- Response size buckets
```

**Summary** - Similar to histogram, calculates percentiles
```
Examples:
- Request duration p50, p95, p99
```

#### 4. Time Series
Every unique combination of metric name + labels = one time series.

**Example:**
```
metric: http_requests_total
labels: method="GET", endpoint="/api/users"
time series: [(timestamp1, value1), (timestamp2, value2), ...]

[
  (2025-01-13T10:00:00Z, 1000),
  (2025-01-13T10:00:15Z, 1025),
  (2025-01-13T10:00:30Z, 1050),
  ...
]
```

---

## How Prometheus Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Application                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Metrics Exporter (Port 9090)                        │ │
│  │                                                       │ │
│  │  Exposes metrics endpoint: /metrics                  │ │
│  │                                                       │ │
│  │  Output:                                             │ │
│  │  # HELP zmq_requests_total Total ZMQ requests       │ │
│  │  # TYPE zmq_requests_total counter                  │ │
│  │  zmq_requests_total{action="ACCOUNT"} 1234          │ │
│  │  zmq_requests_total{action="BALANCE"} 567           │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          ↑
                          │ (scrape every 15s)
                          │
┌─────────────────────────────────────────────────────────────┐
│                   Prometheus Server                          │
│                                                              │
│  1. Scrapes /metrics endpoint every 15 seconds             │
│  2. Stores metrics in time-series database                 │
│  3. Evaluates alerting rules                               │
│  4. Provides PromQL query interface                        │
│                                                              │
│  Storage: ~/prometheus/data/                               │
│  Config: prometheus.yml                                    │
│  Web UI: http://localhost:9091                             │
└─────────────────────────────────────────────────────────────┘
                          ↑
                          │ (query)
                          │
┌─────────────────────────────────────────────────────────────┐
│                        Grafana                               │
│                                                              │
│  - Queries Prometheus for metrics                          │
│  - Displays beautiful dashboards                           │
│  - Sends alerts                                            │
│                                                              │
│  Web UI: http://localhost:3000                             │
└─────────────────────────────────────────────────────────────┘
```

### The Scraping Model

**Traditional monitoring (Push):**
```
App → (pushes data) → Monitoring Server

Problems:
- App needs to know where to send data
- Network issues = lost data
- Hard to discover new services
```

**Prometheus (Pull):**
```
Prometheus → (scrapes) → App's /metrics endpoint

Benefits:
- Prometheus discovers targets
- Can retry on failure
- Central configuration
- See if target is down
```

### Data Flow Example

1. **Your app exposes metrics:**
```
GET http://localhost:9090/metrics

Response:
# HELP mt5_account_balance MT5 account balance
# TYPE mt5_account_balance gauge
mt5_account_balance 10000.50
```

2. **Prometheus scrapes every 15s:**
```
Time        Value
10:00:00    10000.50
10:00:15    10025.00
10:00:30    10050.75
10:00:45    10040.25
```

3. **You query Prometheus:**
```promql
mt5_account_balance

Returns:
mt5_account_balance 10040.25
```

---

## Hands-On Tutorial

### Exercise 1: Start Prometheus

**Goal:** Run Prometheus and understand the basics

1. **Start the MT5 monitoring stack:**
```bash
cd /home/cy/Code/MT5/MT5-Docker

# Start MT5 first
docker-compose up -d mt5zmq

# Start monitoring stack
docker-compose --profile monitoring up -d
```

2. **Verify services are running:**
```bash
docker-compose --profile monitoring ps

# You should see:
# - mt5zmq (running)
# - mt5-exporter (running)
# - mt5-prometheus (running)
# - mt5-grafana (running)
```

3. **Access Prometheus UI:**
- Open browser: http://localhost:9091
- You should see the Prometheus web interface

4. **Explore the UI:**
- **Status → Targets:** See all monitored services
- **Graph:** Query and visualize metrics
- **Alerts:** View active alerts
- **Status → Configuration:** See prometheus.yml

### Exercise 2: Understanding Metrics Endpoint

**Goal:** See what metrics look like

1. **View raw metrics from exporter:**
```bash
curl http://localhost:9090/metrics
```

**You'll see output like:**
```
# HELP zmq_requests_total Total number of ZMQ requests
# TYPE zmq_requests_total counter
zmq_requests_total{action="ACCOUNT"} 45
zmq_requests_total{action="BALANCE"} 120
zmq_requests_total{action="TRADE"} 8

# HELP mt5_account_balance MT5 account balance
# TYPE mt5_account_balance gauge
mt5_account_balance 10000.50

# HELP mt5_connection_status MT5 connection status (1=connected, 0=disconnected)
# TYPE mt5_connection_status gauge
mt5_connection_status 1
```

**Understanding the format:**
```
# HELP <metric_name> <description>       ← Human-readable description
# TYPE <metric_name> <type>              ← Metric type (counter/gauge/etc)
<metric_name>{label1="value1"} <value>  ← Actual metric with labels
```

2. **Check Prometheus scraped it:**
- Go to http://localhost:9091
- Click "Graph"
- Type: `zmq_requests_total`
- Click "Execute"
- See the data!

### Exercise 3: Your First PromQL Query

**Goal:** Learn basic queries

1. **Open Prometheus UI:** http://localhost:9091

2. **Simple query - Get current value:**
```promql
mt5_account_balance
```
Click "Execute" → See current balance

3. **Query with label filtering:**
```promql
zmq_requests_total{action="ACCOUNT"}
```
Shows only ACCOUNT requests

4. **Query multiple labels:**
```promql
zmq_requests_total{action="ACCOUNT",success="true"}
```

5. **View graph over time:**
- After entering query, click "Graph" tab
- See metric over time!

### Exercise 4: Generate Some Metrics

**Goal:** See metrics change in real-time

1. **Run the test script to generate traffic:**
```bash
cd /home/cy/Code/MT5/MT5-Docker

# Make sure MT5 is running
docker-compose ps mt5zmq

# Run tests to generate metrics
.venv/bin/python scripts/test_jsonapi.py
```

2. **Watch metrics update in Prometheus:**
- Go to http://localhost:9091
- Query: `rate(zmq_requests_total[1m])`
- Switch to "Graph" tab
- See the spike in requests!

3. **Query the new data:**
```promql
# Total requests
zmq_requests_total

# Request rate (requests per second)
rate(zmq_requests_total[5m])

# Total requests by action
sum by (action) (zmq_requests_total)
```

---

## PromQL Query Language

### Basic Queries

#### Instant Vector - Current value
```promql
# Get current balance
mt5_account_balance

# Get current connection status
mt5_connection_status
```

#### Label Matching
```promql
# Exact match
zmq_requests_total{action="ACCOUNT"}

# Multiple labels (AND)
zmq_requests_total{action="ACCOUNT",result="success"}

# Regex match
zmq_requests_total{action=~"ACCOUNT|BALANCE"}

# Not equal
zmq_requests_total{action!="TRADE"}
```

### Time-Based Queries

#### Range Vector - Values over time
```promql
# Last 5 minutes of data
zmq_requests_total[5m]

# Last 1 hour
zmq_requests_total[1h]
```

#### Rate - Change per second
```promql
# Requests per second (5-minute average)
rate(zmq_requests_total[5m])

# Errors per second
rate(zmq_errors_total[5m])
```

### Aggregation

#### Sum
```promql
# Total requests across all actions
sum(zmq_requests_total)

# Total by action
sum by (action) (zmq_requests_total)
```

#### Average
```promql
# Average request rate
avg(rate(zmq_requests_total[5m]))
```

#### Max/Min
```promql
# Highest request rate by action
max by (action) (rate(zmq_requests_total[5m]))

# Lowest balance in last hour
min_over_time(mt5_account_balance[1h])
```

### Math Operations

```promql
# Error percentage
rate(zmq_errors_total[5m]) / rate(zmq_requests_total[5m]) * 100

# Free margin percentage
(mt5_account_margin_free / mt5_account_equity) * 100

# Balance change (compare to 1 hour ago)
mt5_account_balance - mt5_account_balance offset 1h
```

### Advanced Queries

#### Percentiles (Histogram)
```promql
# P95 latency
histogram_quantile(0.95, rate(zmq_request_duration_seconds_bucket[5m]))

# P50 (median) latency
histogram_quantile(0.50, rate(zmq_request_duration_seconds_bucket[5m]))

# P99 latency
histogram_quantile(0.99, rate(zmq_request_duration_seconds_bucket[5m]))
```

#### Alerts Logic
```promql
# Connection is down
mt5_connection_status == 0

# High error rate (>10%)
rate(zmq_errors_total[5m]) / rate(zmq_requests_total[5m]) > 0.10

# Low margin (< 20%)
(mt5_account_margin_free / mt5_account_equity) < 0.20
```

---

## Real Examples from MT5-Docker

### Example 1: Monitoring Request Rate

**Question:** How many requests per second is my MT5 API handling?

**Query:**
```promql
rate(zmq_requests_total[5m])
```

**What it does:**
- Takes `zmq_requests_total` (counter)
- Calculates rate of change over 5 minutes
- Returns requests per second

**Result:**
```
zmq_requests_total{action="ACCOUNT"} 2.5
zmq_requests_total{action="BALANCE"} 0.8
zmq_requests_total{action="TRADE"} 0.2
```

**Meaning:**
- 2.5 ACCOUNT requests/sec
- 0.8 BALANCE requests/sec
- 0.2 TRADE requests/sec

**Try it:**
```bash
# In Prometheus UI (http://localhost:9091)
1. Enter: rate(zmq_requests_total[5m])
2. Click "Execute"
3. Switch to "Graph" tab
4. See requests over time!
```

### Example 2: Finding Slow Requests

**Question:** What's the P95 latency of my requests?

**Query:**
```promql
histogram_quantile(0.95, rate(zmq_request_duration_seconds_bucket[5m]))
```

**What it does:**
- Looks at request duration histogram
- Calculates 95th percentile
- Means: 95% of requests are faster than this value

**Example output:**
```
0.045  (45 milliseconds)
```

**Meaning:** 95% of requests finish in under 45ms

**Use case:**
- If P95 > 2 seconds → Houston, we have a problem!
- Alert triggers
- You investigate before users complain

### Example 3: Tracking Account Balance

**Question:** How has my balance changed over the last hour?

**Query:**
```promql
mt5_account_balance - mt5_account_balance offset 1h
```

**What it does:**
- Current balance minus balance from 1 hour ago
- Shows profit/loss

**Example output:**
```
+125.50  (gained $125.50)
```

Or:
```
-50.25  (lost $50.25)
```

### Example 4: Error Rate Monitoring

**Question:** What percentage of requests are failing?

**Query:**
```promql
(
  rate(zmq_errors_total[5m])
  /
  rate(zmq_requests_total[5m])
) * 100
```

**What it does:**
- Calculates error rate
- Divides by total request rate
- Converts to percentage

**Example output:**
```
0.15  (0.15% error rate = 99.85% success rate)
```

**Alert rule:**
```yaml
- alert: HighErrorRate
  expr: |
    (rate(zmq_errors_total[5m]) / rate(zmq_requests_total[5m])) > 0.10
  annotations:
    summary: "Error rate above 10%!"
```

---

## Hands-On Exercises

### Exercise 5: Create Custom Queries

**Task 1: Find total requests in last 5 minutes**
```promql
# Try to write this yourself!
# Hint: Use increase() function

# Solution (don't peek!)
increase(zmq_requests_total[5m])
```

**Task 2: Calculate average balance over 1 hour**
```promql
# Your turn!

# Solution:
avg_over_time(mt5_account_balance[1h])
```

**Task 3: Find if any errors occurred in last 10 minutes**
```promql
# Hint: Use increase() and > 0

# Solution:
increase(zmq_errors_total[10m]) > 0
```

### Exercise 6: Understanding Alert Rules

Let's look at an alert rule from `prometheus/alerts.yml`:

```yaml
- alert: MT5ConnectionDown
  expr: mt5_connection_status == 0
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "MT5 connection is down"
    description: "MT5 is not responding"
```

**Breaking it down:**
- `expr:` The PromQL query
- `for: 2m` Must be true for 2 minutes (avoids flapping)
- `severity: critical` How serious is this?
- `annotations:` Human-readable messages

**Try it:**
1. Stop MT5:
```bash
docker stop mt5zmq
```

2. Wait 2 minutes

3. Check Prometheus alerts:
- Go to http://localhost:9091/alerts
- See "MT5ConnectionDown" firing!

4. Restart MT5:
```bash
docker start mt5zmq
```

5. Alert clears automatically

---

## Best Practices

### 1. Metric Naming

**Good:**
```
mt5_account_balance
zmq_requests_total
zmq_request_duration_seconds
```

**Bad:**
```
balance  (too generic)
reqs  (not clear)
time  (ambiguous)
```

**Convention:**
- `<namespace>_<metric>_<unit>`
- Use base units (seconds, bytes, not milliseconds, megabytes)
- Suffix counters with `_total`
- Suffix gauges with their unit

### 2. Label Usage

**Good:**
```promql
zmq_requests_total{action="ACCOUNT", result="success"}
```

**Bad (High cardinality):**
```promql
zmq_requests_total{user_id="12345"}  # Too many unique values!
zmq_requests_total{timestamp="..."}   # Time is not a label!
```

**Rule:** Labels should have limited, predictable values

### 3. Query Performance

**Efficient:**
```promql
# Query last 5 minutes
rate(zmq_requests_total[5m])
```

**Inefficient:**
```promql
# Query last 7 days (slow!)
rate(zmq_requests_total[7d])
```

**Rule:** Use appropriate time ranges

### 4. Alert Design

**Good alert:**
```yaml
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(zmq_request_duration_seconds_bucket[5m])) > 2
  for: 10m  # Sustained high latency
```

**Bad alert:**
```yaml
- alert: AnyError
  expr: zmq_errors_total > 0
  for: 10s  # Too sensitive!
```

**Rule:** Alerts should be actionable and not noisy

---

## Troubleshooting

### Issue 1: No Data in Prometheus

**Symptoms:** Queries return empty results

**Debug steps:**

1. **Check if exporter is running:**
```bash
docker-compose --profile monitoring ps mt5-exporter
```

2. **Check exporter logs:**
```bash
docker logs mt5-exporter
```

3. **Test metrics endpoint:**
```bash
curl http://localhost:9090/metrics
```

4. **Check Prometheus targets:**
- Go to http://localhost:9091/targets
- Is target "UP" or "DOWN"?

5. **Check Prometheus logs:**
```bash
docker logs mt5-prometheus
```

### Issue 2: Scrape Failures

**In Prometheus UI → Status → Targets, you see errors**

**Common causes:**

1. **Port not accessible:**
```bash
# Test connection
nc -zv localhost 9090
```

2. **Wrong endpoint:**
```bash
# Check endpoint in prometheus.yml
docker exec mt5-prometheus cat /etc/prometheus/prometheus.yml
```

3. **Firewall blocking:**
```bash
# Check if Docker networks are correct
docker network inspect mt5-docker_default
```

### Issue 3: Queries Return Unexpected Results

**Problem:** Query shows weird numbers

**Debug:**

1. **Check raw metrics:**
```bash
curl http://localhost:9090/metrics | grep metric_name
```

2. **Check time range:**
```promql
# Are you looking at the right time?
mt5_account_balance[5m]
```

3. **Check labels:**
```promql
# Are labels what you expect?
zmq_requests_total{action="ACCOUNT"}
```

4. **Use rate() for counters:**
```promql
# Wrong (counter raw value)
zmq_requests_total

# Right (rate of change)
rate(zmq_requests_total[5m])
```

---

## Practice Challenges

### Challenge 1: Basic Monitoring

**Setup a dashboard that shows:**
1. Current MT5 connection status
2. Request rate over last 15 minutes
3. Current account balance
4. Error count in last hour

**Queries to use:**
```promql
# 1. Connection status
mt5_connection_status

# 2. Request rate
rate(zmq_requests_total[15m])

# 3. Balance
mt5_account_balance

# 4. Error count
increase(zmq_errors_total[1h])
```

### Challenge 2: Performance Analysis

**Analyze request performance:**
1. What's the average request latency?
2. What's the P50, P95, P99 latency?
3. Which action type is slowest?

**Queries:**
```promql
# 1. Average latency
avg(rate(zmq_request_duration_seconds_sum[5m]) / rate(zmq_request_duration_seconds_count[5m]))

# 2. Percentiles
histogram_quantile(0.50, rate(zmq_request_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(zmq_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(zmq_request_duration_seconds_bucket[5m]))

# 3. Slowest action
topk(1, avg by (action) (rate(zmq_request_duration_seconds_sum[5m]) / rate(zmq_request_duration_seconds_count[5m])))
```

### Challenge 3: Create an Alert

**Create an alert that fires when:**
- Account balance drops by more than 5% in 30 minutes

**Solution:**
```yaml
- alert: SignificantBalanceDrop
  expr: |
    (
      (mt5_account_balance - mt5_account_balance offset 30m)
      /
      mt5_account_balance offset 30m
    ) < -0.05
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Account balance dropped >5% in 30 minutes"
    description: "Balance changed from {{ $value | humanize }}"
```

---

## Next Steps

**You've learned:**
- ✓ What monitoring is and why it matters
- ✓ How Prometheus works (scraping, storage, querying)
- ✓ Metric types (counter, gauge, histogram)
- ✓ PromQL basics and advanced queries
- ✓ How to create alerts
- ✓ Real-world examples from MT5-Docker

**Continue learning:**
- Next tutorial: [Grafana Dashboards](03_GRAFANA_GUIDE.md)
- Practice: Write more complex queries
- Read: [Prometheus Best Practices](https://prometheus.io/docs/practices/)

---

## Quick Reference

### Common Functions

```promql
# Rate (for counters)
rate(metric[5m])

# Increase (for counters)
increase(metric[5m])

# Aggregation
sum(metric)
avg(metric)
max(metric)
min(metric)

# Over time
avg_over_time(metric[1h])
max_over_time(metric[1h])
min_over_time(metric[1h])

# Math
metric1 + metric2
metric1 - metric2
metric1 * metric2
metric1 / metric2

# Comparison
metric > 100
metric < 50
metric == 1
metric != 0
```

### Useful Queries

```promql
# Request rate
rate(requests_total[5m])

# Error rate percentage
(rate(errors_total[5m]) / rate(requests_total[5m])) * 100

# Latency P95
histogram_quantile(0.95, rate(duration_bucket[5m]))

# Memory usage percentage
(memory_used / memory_total) * 100

# Change from 1 hour ago
metric - metric offset 1h
```
