# Grafana Dashboards Tutorial - From Zero to Hero

**Time to complete:** 60-90 minutes
**Prerequisites:** Basic Prometheus knowledge (complete Tutorial 02 first)

---

## Table of Contents

1. [Conceptual Understanding](#conceptual-understanding)
2. [How Grafana Works](#how-grafana-works)
3. [Hands-On Tutorial](#hands-on-tutorial)
4. [Building Dashboards](#building-dashboards)
5. [Real Examples](#real-examples)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Conceptual Understanding

### What is Grafana?

**Grafana** is a visualization and analytics platform that creates beautiful dashboards from your metrics data.

**Think of it this way:**
- **Prometheus** = Your data warehouse (stores all the numbers)
- **Grafana** = Your beautiful storefront (displays the numbers nicely)

**Without Grafana:**
```
Want to see request rate?
→ Go to Prometheus
→ Type PromQL query
→ See basic graph
→ Want another metric?
→ Type another query
→ Repeat...
```

**With Grafana:**
```
Open one dashboard and see:
- Request rate (live graph)
- Error rate (colorful gauge)
- Account balance (big number)
- Latency (multiple lines)
- All updating in real-time!
```

### Why Use Grafana?

1. **Beautiful Visualizations**
   - Professional-looking dashboards
   - Multiple visualization types
   - Color-coded alerts

2. **Multiple Data Sources**
   - Prometheus, InfluxDB, Elasticsearch, MySQL, etc.
   - Combine data from different sources

3. **Alerting**
   - Visual alerts on dashboards
   - Email, Slack, PagerDuty notifications

4. **Templating**
   - Create dynamic dashboards
   - Filter by server, environment, etc.

5. **Sharing**
   - Share dashboards with team
   - Export/import JSON
   - Public dashboards

### Key Concepts

#### 1. Data Source
Where Grafana gets its data from.

**For our project:**
```
Data Source: Prometheus
URL: http://prometheus:9090
```

#### 2. Dashboard
A collection of panels showing different metrics.

**Example dashboard sections:**
- System Overview
- Performance Metrics
- Business Metrics
- Alerts

#### 3. Panel
A single visualization (graph, gauge, table, etc.).

**Panel types:**
- Time series (line graphs)
- Gauge (speedometer-style)
- Stat (big number)
- Bar chart
- Heatmap
- Table

#### 4. Query
PromQL query that fetches data for a panel.

**Example:**
```promql
rate(zmq_requests_total[5m])
```

#### 5. Variables
Dynamic filters for your dashboard.

**Example:**
```
Variable: $timeframe
Values: 5m, 15m, 1h, 6h
Query uses: rate(metric[$timeframe])
```

---

## How Grafana Works

### Architecture

```
┌──────────────────────────────────────────────┐
│             User's Browser                    │
│                                               │
│  Viewing: http://localhost:3000              │
└──────────────────────────────────────────────┘
                    ↑ ↓
        (HTTP requests/responses)
                    ↑ ↓
┌──────────────────────────────────────────────┐
│            Grafana Server                     │
│                                               │
│  1. Serves web interface                     │
│  2. Stores dashboards                        │
│  3. Queries data sources                     │
│  4. Sends alerts                             │
│                                               │
│  Port: 3000                                  │
│  Storage: /var/lib/grafana/                  │
└──────────────────────────────────────────────┘
                    ↑ ↓
          (PromQL queries)
                    ↑ ↓
┌──────────────────────────────────────────────┐
│          Prometheus Server                    │
│                                               │
│  Returns metric data                         │
│                                               │
│  URL: http://prometheus:9090                 │
└──────────────────────────────────────────────┘
```

### Data Flow

1. **You open Grafana dashboard**
2. **Grafana sends PromQL queries to Prometheus**
3. **Prometheus returns metric data**
4. **Grafana transforms data for visualization**
5. **Browser displays beautiful charts**

**Example:**
```
User opens dashboard
    ↓
Grafana executes:
    - Query 1: rate(zmq_requests_total[5m])
    - Query 2: mt5_account_balance
    - Query 3: histogram_quantile(0.95, ...)
    ↓
Prometheus returns data for each query
    ↓
Grafana creates:
    - Panel 1: Line graph
    - Panel 2: Big number
    - Panel 3: Gauge
    ↓
You see the dashboard!
```

---

## Hands-On Tutorial

### Exercise 1: Access Grafana

1. **Start Grafana:**
```bash
cd /home/cy/Code/MT5/MT5-Docker

# If not already running
docker-compose --profile monitoring up -d grafana
```

2. **Access Grafana:**
- Open browser: http://localhost:3000
- **Username:** `admin`
- **Password:** `admin`
- (You'll be prompted to change password - skip for now)

3. **Explore the interface:**
- **Left sidebar:** Main navigation
- **Dashboards:** View existing dashboards
- **Explore:** Ad-hoc queries
- **Alerting:** Manage alerts
- **Configuration:** Settings

### Exercise 2: Connect Prometheus Data Source

**Goal:** Tell Grafana where to get data

1. **Add data source:**
- Click **Configuration** (gear icon) → **Data sources**
- Click **Add data source**
- Select **Prometheus**

2. **Configure:**
```
Name: Prometheus
URL: http://prometheus:9090
Access: Server (default)
```

3. **Test connection:**
- Scroll down
- Click **Save & test**
- Should see: ✓ "Data source is working"

### Exercise 3: Explore Data

**Goal:** Run ad-hoc queries to understand your data

1. **Go to Explore:**
- Click **Explore** (compass icon) in sidebar

2. **Run your first query:**
```promql
mt5_account_balance
```
- Type the query in the query editor
- Click **Run query**
- See the metric value!

3. **Try more queries:**
```promql
# Connection status
mt5_connection_status

# Request rate
rate(zmq_requests_total[5m])

# All metrics (lists everything)
{__name__=~".+"}
```

4. **Change visualization:**
- Below the graph, try different visualization types:
  - Time series
  - Stat
  - Gauge
  - Table

### Exercise 4: Create Your First Dashboard

**Goal:** Build a simple dashboard from scratch

1. **Create new dashboard:**
- Click **+** (plus icon) → **Dashboard**
- Click **Add new panel**

2. **Configure panel:**
```
Query: mt5_account_balance
```

3. **Customize:**
- **Panel title:** "MT5 Account Balance"
- **Visualization:** Stat (big number)
- **Unit:** currency (USD)
- **Color:** Green

4. **Save panel:**
- Click **Apply** (top right)

5. **Add another panel:**
- Click **Add panel** (top right)
- Query: `rate(zmq_requests_total[5m])`
- Title: "Request Rate"
- Visualization: Time series
- Click **Apply**

6. **Save dashboard:**
- Click **Save dashboard** (disk icon)
- Name: "My First Dashboard"
- Click **Save**

Congratulations! You created your first dashboard! 🎉

---

## Building Dashboards

### Dashboard Best Practices

#### 1. Layout Organization

**Good layout:**
```
┌─────────────────────────────────────────┐
│  [Connection Status]  [Current Balance] │  ← Top: Most important metrics
├─────────────────────────────────────────┤
│  [Request Rate Graph - Full Width]      │  ← Middle: Trends over time
├─────────────────────────────────────────┤
│  [Error Count]  [Latency]  [Margin]     │  ← Bottom: Supporting metrics
└─────────────────────────────────────────┘
```

**Bad layout:**
```
Random metrics scattered everywhere - hard to understand!
```

#### 2. Color Coding

**Use colors meaningfully:**
- 🟢 Green: Good/Healthy
- 🟡 Yellow: Warning
- 🔴 Red: Critical/Error
- 🔵 Blue: Neutral/Info

**Example:**
```
Connection Status:
- 1 (connected) → Green
- 0 (disconnected) → Red

Error Rate:
- < 1% → Green
- 1-5% → Yellow
- > 5% → Red
```

#### 3. Panel Types

**Choose the right visualization:**

**Big Number (Stat):**
```
Use for: Current values
Example: Account balance, connection status
```

**Line Graph (Time series):**
```
Use for: Trends over time
Example: Request rate, latency, balance changes
```

**Gauge:**
```
Use for: Percentage or range
Example: CPU usage, margin level, error rate
```

**Bar Chart:**
```
Use for: Comparing categories
Example: Requests by action type
```

**Table:**
```
Use for: Detailed data
Example: List of open positions, recent errors
```

### Panel Configuration

#### Basic Query Configuration

1. **Add query:**
```promql
rate(zmq_requests_total[5m])
```

2. **Add legend:**
```
Legend: {{action}}  # Shows action label in legend
```

3. **Set min/max:**
```
Min: 0
Max: Auto (or specific value)
```

#### Thresholds

**Set color thresholds:**
```
Thresholds:
- Base: Green
- 0.8 (80%): Yellow
- 0.9 (90%): Red
```

**Example - Error rate:**
```
Query: (rate(zmq_errors_total[5m]) / rate(zmq_requests_total[5m])) * 100
Unit: Percent (0-100)
Thresholds:
  - 0: Green
  - 1: Yellow  (1% errors)
  - 5: Red     (5% errors)
```

#### Transformations

**Transform data before displaying:**

**Example - Show only last value:**
```
Transformations:
1. Add transformation → Reduce
2. Calculation: Last (not null)
```

**Example - Calculate difference:**
```
Transformations:
1. Add transformation → Add field from calculation
2. Mode: Binary operation
3. Operation: difference
```

---

## Real Examples

### Example 1: Connection Status Panel

**What we want:** Big indicator showing if MT5 is connected

**Configuration:**
```yaml
Query: mt5_connection_status
Visualization: Stat
Unit: None
Mapping:
  0 → "Disconnected" (Red)
  1 → "Connected" (Green)
Thresholds:
  0: Red
  1: Green
```

**How to create:**
1. Add panel
2. Query: `mt5_connection_status`
3. Visualization → Stat
4. Value mappings:
   - Add: 0 → Text: "Disconnected"
   - Add: 1 → Text: "Connected"
5. Thresholds:
   - Base (0): Red
   - 1: Green

### Example 2: Request Rate Graph

**What we want:** Line graph showing requests per second by action type

**Configuration:**
```yaml
Query: rate(zmq_requests_total[5m])
Legend: {{action}}
Visualization: Time series
Y-axis: Requests/sec
```

**How to create:**
1. Add panel
2. Query: `rate(zmq_requests_total[5m])`
3. Legend: `{{action}}`
4. Visualization → Time series
5. Field config → Unit → "reqps" (requests per second)
6. Multiple series will show automatically!

### Example 3: Balance with Trend

**What we want:** Current balance + sparkline showing trend

**Configuration:**
```yaml
Query A: mt5_account_balance
Visualization: Stat
Graph mode: Area
Color: Value-based
Unit: currency (USD)
```

**How to create:**
1. Add panel
2. Query: `mt5_account_balance`
3. Visualization → Stat
4. Show: Value and graph
5. Graph mode: Area
6. Unit → currency → USD ($)
7. Decimals: 2

### Example 4: Latency Percentiles

**What we want:** P50, P95, P99 latency on same graph

**Configuration:**
```yaml
Query A: histogram_quantile(0.50, rate(zmq_request_duration_seconds_bucket[5m]))
Query B: histogram_quantile(0.95, rate(zmq_request_duration_seconds_bucket[5m]))
Query C: histogram_quantile(0.99, rate(zmq_request_duration_seconds_bucket[5m]))
Legend A: p50
Legend B: p95
Legend C: p99
```

**How to create:**
1. Add panel
2. Add Query A: `histogram_quantile(0.50, ...)`
   - Legend: `p50`
3. Click "+ Query"
4. Add Query B: `histogram_quantile(0.95, ...)`
   - Legend: `p95`
5. Add Query C: `histogram_quantile(0.99, ...)`
   - Legend: `p99`
6. Unit → Time → seconds (s)
7. All three lines show on same graph!

---

## Hands-On Exercises

### Exercise 5: Import Existing Dashboard

**Goal:** Import the pre-built MT5 dashboard

1. **Navigate to import:**
- Click **+** → **Import**

2. **Import from file:**
- Click **Upload JSON file**
- Select: `/home/cy/Code/MT5/MT5-Docker/monitoring/grafana/dashboards/mt5-dashboard.json`
- Click **Load**

3. **Configure:**
- Select Prometheus data source
- Click **Import**

4. **Explore the dashboard:**
- See all 7 pre-configured panels
- Understand how each is built
- Click **Edit** on any panel to see configuration

### Exercise 6: Modify Existing Panel

**Goal:** Customize a panel

1. **Edit panel:**
- Click on panel title → **Edit**

2. **Change time range:**
- Top right: Change from "Last 6 hours" to "Last 1 hour"
- See how data adjusts

3. **Change colors:**
- Panel → Standard options → Color scheme
- Try different color schemes

4. **Add threshold:**
- Panel → Thresholds → Add threshold
- Set value and color

5. **Save:**
- Click **Apply**
- Save dashboard

### Exercise 7: Create Multi-Stat Row

**Goal:** Create a row of stats showing key metrics

1. **Create new dashboard**

2. **Add 4 panels in a row:**

**Panel 1 - Connection:**
```
Query: mt5_connection_status
Type: Stat
Size: 1/4 width
```

**Panel 2 - Balance:**
```
Query: mt5_account_balance
Type: Stat
Size: 1/4 width
Unit: USD
```

**Panel 3 - Request Rate:**
```
Query: sum(rate(zmq_requests_total[5m]))
Type: Stat
Size: 1/4 width
Unit: reqps
```

**Panel 4 - Error Count:**
```
Query: increase(zmq_errors_total[1h])
Type: Stat
Size: 1/4 width
```

3. **Adjust layout:**
- Drag panels to resize
- Arrange in single row

4. **Save dashboard:** "Key Metrics"

---

## Advanced Features

### Variables

**Create dynamic dashboards with variables**

**Example - Time Range Variable:**
1. Dashboard settings (gear icon)
2. Variables → Add variable
3. Type: Custom
4. Name: `timerange`
5. Custom options: `5m,15m,1h,6h,24h`
6. Use in query: `rate(metric[$timerange])`

### Annotations

**Mark events on graphs**

**Example - Deployment markers:**
```
Show when code was deployed
Show when alerts fired
Show when config changed
```

### Alerts

**Get notified when things go wrong**

**Example - High latency alert:**
1. Edit panel
2. Alert tab
3. Create alert rule:
```
WHEN: avg() of query(A, 5m, now)
IS ABOVE: 2
FOR: 10m
SEND TO: email/slack
```

---

## Best Practices

### 1. Dashboard Design

**Do:**
- ✓ Most important metrics at top
- ✓ Use consistent time ranges
- ✓ Group related metrics
- ✓ Use descriptive titles
- ✓ Add panel descriptions

**Don't:**
- ✗ Too many panels (keeps it under 12)
- ✗ Tiny panels (hard to read)
- ✗ Random organization
- ✗ Excessive decimals

### 2. Query Performance

**Do:**
- ✓ Use appropriate time ranges
- ✓ Limit data points with rate/increase
- ✓ Use recording rules for complex queries

**Don't:**
- ✗ Query huge time ranges
- ✗ Use regex unnecessarily
- ✗ Create too many series

### 3. Color Usage

**Meaningful colors:**
```
Green: Healthy, successful, good
Yellow: Warning, degraded
Red: Critical, failed, bad
Blue: Neutral, informational
```

### 4. Units

**Always set appropriate units:**
```
Currency: currency → USD ($)
Percentage: percent (0-100)
Time: seconds (s), milliseconds (ms)
Bytes: bytes (B)
Rate: operations per second (ops)
```

---

## Troubleshooting

### Issue 1: "No Data"

**Symptoms:** Panel shows "No data"

**Solutions:**

1. **Check time range:**
- Is time range too far in past?
- Adjust to "Last 1 hour"

2. **Check query:**
```bash
# Test in Prometheus first
# Go to http://localhost:9091
# Run the same query
```

3. **Check data source:**
- Configuration → Data sources
- Test connection

4. **Check if metric exists:**
```bash
curl http://localhost:9090/metrics | grep metric_name
```

### Issue 2: Graph Looks Wrong

**Symptoms:** Weird lines, unexpected values

**Solutions:**

1. **Check query type:**
```promql
# For counters, use rate()
rate(counter_total[5m])

# Not raw counter
counter_total  # Wrong!
```

2. **Check units:**
- Are you showing bytes as currency?
- Set correct unit in panel config

3. **Check time range:**
- Query range should match display range

### Issue 3: Dashboard Loads Slowly

**Symptoms:** Dashboard takes long to load

**Solutions:**

1. **Reduce queries:**
- Limit number of panels
- Use simpler queries

2. **Optimize queries:**
```promql
# Better
rate(metric{job="specific"}[5m])

# Worse (queries everything)
rate(metric[5m])
```

3. **Adjust refresh rate:**
- Top right: Change from "5s" to "30s" or "1m"

---

## Practice Challenges

### Challenge 1: Trading Dashboard

**Create a dashboard showing:**
1. Current balance (big number with trend)
2. Equity over time (line graph)
3. Margin level gauge (0-100%)
4. Trade count in last hour

**Queries:**
```promql
# 1. Balance
mt5_account_balance

# 2. Equity
mt5_account_equity

# 3. Margin level
(mt5_account_margin_free / mt5_account_equity) * 100

# 4. Trade count
increase(zmq_requests_total{action="TRADE"}[1h])
```

### Challenge 2: Performance Dashboard

**Create a dashboard showing:**
1. Request rate by action (stacked area chart)
2. Latency percentiles (line graph)
3. Error rate percentage (gauge)
4. Top 5 slowest actions (bar chart)

**Bonus:** Add threshold colors!

### Challenge 3: Alert Dashboard

**Create a dashboard that:**
1. Shows all firing alerts
2. Shows alert history
3. Color-codes by severity
4. Links to relevant dashboards

---

## Next Steps

**You've learned:**
- ✓ What Grafana is and how it works
- ✓ How to connect data sources
- ✓ How to create and customize dashboards
- ✓ Panel types and when to use them
- ✓ Best practices for dashboard design

**Continue learning:**
- Build more dashboards
- Try advanced features (variables, annotations, alerts)
- Read: [Grafana Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)
- Explore: [Grafana Dashboard Gallery](https://grafana.com/grafana/dashboards/)

---

## Quick Reference

### Common Panel Types

| Type | Use Case | Example |
|------|----------|---------|
| Stat | Current value | Balance, connection status |
| Time series | Trends | Request rate, latency |
| Gauge | Percentage | CPU usage, error rate |
| Bar chart | Comparison | Requests by action |
| Table | Detailed data | Error list, trades |

### Useful Query Patterns

```promql
# Current value
metric_name

# Rate of change
rate(metric_total[5m])

# Percentage
(metric_a / metric_b) * 100

# Percentile
histogram_quantile(0.95, rate(metric_bucket[5m]))

# Sum by label
sum by (label) (metric)

# Top N
topk(5, metric)
```

### Keyboard Shortcuts

```
Ctrl/Cmd + S     Save dashboard
Ctrl/Cmd + H     Toggle help
d                Dashboard settings
e                Edit panel (when selected)
v                View panel in fullscreen
Esc              Exit edit mode
```
