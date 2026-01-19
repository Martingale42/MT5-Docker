# Querying Logs with LogsQL

Learn to search, filter, and analyze logs in VictoriaLogs.

## Prerequisites

- Monitoring stack running (`docker compose up -d`)
- Access to http://localhost:9428/select/vmui (VictoriaLogs UI)
- Some logs generated (run `docker restart grafana` to generate some)

## Understanding Log Structure

Each log entry in VictoriaLogs has:

| Field | Description | Example |
|-------|-------------|---------|
| `_time` | Timestamp | `2024-01-19T10:30:45Z` |
| `_msg` | The log message content | `"[WATCHDOG] MT5 is running"` |
| `_stream` | Labels identifying source | `{service="mt5zmq"}` |
| Custom fields | Added by Vector | `service`, `container`, etc. |

Example log entry:
```json
{
  "_time": "2024-01-19T10:30:45.123Z",
  "_msg": "{\"message\":\"Plugin loaded\",\"level\":\"info\"}",
  "_stream": "{container=\"grafana\",service=\"grafana\"}",
  "service": "grafana",
  "container": "grafana"
}
```

## LogsQL Basics

### Simple Text Search

Search for any logs containing a word:

```logsql
error
```

This finds logs where `_msg` contains "error" (case-insensitive).

### Multiple Words (AND)

All words must be present:

```logsql
error connection
```

Equivalent to:
```logsql
error AND connection
```

### OR Conditions

Either word:

```logsql
error OR warning
```

### NOT Conditions

Exclude matches:

```logsql
error NOT timeout
```

### Phrases

Exact phrase match:

```logsql
"connection refused"
```

## Filtering by Labels

### Filter by Service

```logsql
service:mt5zmq
```

### Filter by Container

```logsql
container:grafana
```

### Combine Label and Text

```logsql
service:mt5zmq error
```

This finds logs from mt5zmq containing "error".

### Multiple Label Values

```logsql
service:(mt5zmq OR grafana)
```

### Wildcard in Labels

```logsql
service:mt5*
```

## Time Filters

### Relative Time

```logsql
_time:5m      # last 5 minutes
_time:1h      # last 1 hour
_time:24h     # last 24 hours
_time:7d      # last 7 days
```

### Absolute Time Range

```logsql
_time:[2024-01-19T00:00:00Z, 2024-01-19T12:00:00Z]
```

### Combine with Other Filters

```logsql
service:mt5zmq error _time:1h
```

## Advanced Queries

### Regular Expressions

Use `~` for regex matching:

```logsql
_msg:~"error.*timeout"
```

Match IP addresses:

```logsql
_msg:~"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
```

### Case-Sensitive Search

By default, searches are case-insensitive. For case-sensitive:

```logsql
_msg:="ERROR"
```

### Field Existence

Logs that have a specific field:

```logsql
level:*
```

### Numeric Comparisons

If you have numeric fields:

```logsql
status_code:>400
```

## Practical Examples

### Find All Errors

```logsql
error OR ERROR OR Error OR fail OR FAIL OR exception
```

### MT5 Watchdog Messages

```logsql
service:mt5zmq WATCHDOG
```

### Grafana Plugin Issues

```logsql
service:grafana plugin
```

### Authentication Failures

```logsql
auth fail OR authentication failed OR password
```

### Network Issues

```logsql
connection refused OR timeout OR unreachable
```

### Logs in Last Hour Excluding Health Checks

```logsql
_time:1h NOT healthcheck NOT "health check"
```

### Find Slow Operations

```logsql
slow OR "took" OR latency OR duration
```

## Using the Web UI

### Basic Usage

1. Open http://localhost:9428/select/vmui
2. Enter your query in the text box
3. Set time range (top right): "Last 5 minutes", "Last 1 hour", etc.
4. Click **Execute Query**

### Understanding Results

Results show:
- **Time**: When the log was generated
- **Stream**: Labels (service, container)
- **Message**: The actual log content

### View Options

- **Group**: Groups logs by stream (default)
- **Table**: Shows as a table with columns
- **JSON**: Raw JSON output

### Tips

1. **Start broad, then narrow**: Begin with `*` to see all logs, then add filters
2. **Use the time range picker**: Adjust to find relevant timeframes
3. **Click on labels**: Clicking a label value adds it as a filter

## Querying via API

### Basic Query

```bash
curl -s "http://localhost:9428/select/logsql/query?query=*&limit=10"
```

### With Filters

```bash
# URL encode special characters
curl -s "http://localhost:9428/select/logsql/query?query=service%3Amt5zmq&limit=20"
```

### Time Range

```bash
curl -s "http://localhost:9428/select/logsql/query?query=*&start=2024-01-19T00:00:00Z&end=2024-01-19T12:00:00Z"
```

### Output Formats

```bash
# Default JSON lines
curl -s "http://localhost:9428/select/logsql/query?query=*"

# Tail (streaming)
curl -s "http://localhost:9428/select/logsql/tail?query=service:mt5zmq"
```

## Common Troubleshooting Scenarios

### "Why did MT5 restart?"

```logsql
service:mt5zmq (restart OR crash OR killed OR OOM OR "out of memory") _time:24h
```

### "What happened at a specific time?"

```logsql
_time:[2024-01-19T14:30:00Z, 2024-01-19T14:35:00Z]
```

### "Are there connection issues?"

```logsql
connection AND (refused OR timeout OR reset OR failed) _time:1h
```

### "What errors occurred today?"

```logsql
(error OR exception OR fail) _time:24h
```

### "Is the watchdog detecting problems?"

```logsql
service:mt5zmq WATCHDOG _time:1h
```

## Statistics and Aggregations

VictoriaLogs supports basic aggregations:

### Count Logs by Service

```logsql
* | stats count() by (service)
```

### Count Errors per Hour

```logsql
error | stats by (_time:1h) count()
```

### Unique Values

```logsql
* | stats count() by (container)
```

## Performance Tips

1. **Always use time filters**: Queries are faster with `_time:` constraints
2. **Filter by stream first**: `service:mt5zmq` before text search
3. **Limit results**: Use `limit` parameter for exploratory queries
4. **Avoid broad regex**: `.*` is slow; be specific

## LogsQL vs Other Query Languages

| Feature | LogsQL | Loki (LogQL) | Elasticsearch |
|---------|--------|--------------|---------------|
| Simple search | `error` | `{} \|= "error"` | `error` |
| Label filter | `service:mt5zmq` | `{service="mt5zmq"}` | `service:mt5zmq` |
| Regex | `~"pattern"` | `\|~ "pattern"` | `/pattern/` |
| Time | `_time:1h` | via UI | `@timestamp:[now-1h TO now]` |

LogsQL is designed to be intuitive and SQL-like, making it easy to learn.

## Reference

### Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `AND` | Both conditions | `error AND timeout` |
| `OR` | Either condition | `error OR warning` |
| `NOT` | Exclude | `error NOT debug` |
| `:` | Label filter | `service:mt5zmq` |
| `:=` | Exact match | `level:="ERROR"` |
| `:~` | Regex match | `_msg:~"error.*"` |
| `:>` | Greater than | `code:>400` |
| `:<` | Less than | `latency:<100` |

### Special Fields

| Field | Description |
|-------|-------------|
| `_time` | Log timestamp |
| `_msg` | Log message |
| `_stream` | Stream labels |
| `*` | Match any value |

### Time Units

| Unit | Description |
|------|-------------|
| `s` | Seconds |
| `m` | Minutes |
| `h` | Hours |
| `d` | Days |
| `w` | Weeks |

## Further Reading

- [VictoriaLogs Documentation](https://docs.victoriametrics.com/victorialogs/)
- [LogsQL Reference](https://docs.victoriametrics.com/victorialogs/logsql/)
