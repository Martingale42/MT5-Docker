# Historical Data API Guide

## Overview

MT5 JsonAPI provides comprehensive access to historical market data for both bars (OHLCV) and ticks (bid/ask). You can either retrieve the data directly via the API or write it to CSV files on the MT5 terminal.

## Command: HISTORY

The `HISTORY` action retrieves historical market data with various options.

### Request Format

```python
{
    "action": "HISTORY",
    "actionType": "DATA" | "WRITE" | "TRADES",
    "symbol": "BTCUSD",
    "chartTF": "M1" | "M5" | "H1" | "D1" | "TICK",
    "fromDate": 1234567890,  # Unix timestamp
    "toDate": 1234567890     # Unix timestamp (optional, defaults to now)
}
```

### Action Types

#### 1. DATA - Get Historical Bar Data

Retrieve OHLCV bar data directly via the API.

**Request:**
```python
import zmq
import json
import time

context = zmq.Context()

# System socket
system_socket = context.socket(zmq.REQ)
system_socket.connect("tcp://localhost:2201")

# Data socket
data_socket = context.socket(zmq.PULL)
data_socket.connect("tcp://localhost:2202")

# Request last 7 days of M1 data
command = {
    "action": "HISTORY",
    "actionType": "DATA",
    "symbol": "BTCUSD",
    "chartTF": "M1",
    "fromDate": int(time.time()) - (7 * 24 * 60 * 60),
    "toDate": int(time.time())
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()  # "OK"

# Receive data
data_socket.setsockopt(zmq.RCVTIMEO, 10000)  # 10 second timeout
response = data_socket.recv_string()
data = json.loads(response)
```

**Response Format:**
```json
{
  "symbol": "BTCUSD",
  "timeframe": "M1",
  "data": [
    [timestamp, open, high, low, close, tick_volume],
    [1699900800, 35234.50, 35250.00, 35200.00, 35245.25, 125],
    [1699900860, 35245.25, 35260.00, 35240.00, 35255.00, 98],
    ...
  ]
}
```

**Data Array Structure:**
- `[0]`: Unix timestamp (seconds)
- `[1]`: Open price
- `[2]`: High price
- `[3]`: Low price
- `[4]`: Close price
- `[5]`: Tick volume (number of ticks in the bar)

#### 2. DATA - Get Historical Tick Data

Retrieve individual tick data (bid/ask prices).

**Request:**
```python
command = {
    "action": "HISTORY",
    "actionType": "DATA",
    "symbol": "BTCUSD",
    "chartTF": "TICK",  # ← Use TICK for tick data
    "fromDate": int(time.time()) - 3600,  # Last hour
    "toDate": int(time.time())
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()

response = data_socket.recv_string()
data = json.loads(response)
```

**Response Format:**
```json
{
  "symbol": "BTCUSD",
  "timeframe": "TICK",
  "data": [
    [tick_time_ms, bid, ask],
    [1699900800123, 35234.50, 35236.75],
    [1699900800456, 35235.00, 35237.25],
    ...
  ]
}
```

**Data Array Structure:**
- `[0]`: Unix timestamp in milliseconds
- `[1]`: Bid price
- `[2]`: Ask price

#### 3. WRITE - Export to CSV File

Write historical data to a CSV file on the MT5 terminal's local file system.

**Request:**
```python
command = {
    "action": "HISTORY",
    "actionType": "WRITE",
    "symbol": "BTCUSD",
    "chartTF": "M1",
    "fromDate": int(time.time()) - (30 * 24 * 60 * 60),  # Last 30 days
    "toDate": int(time.time())
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()
```

**File Location:**
- Path: `{MT5_DATA_PATH}/Files/Data/{SYMBOL}-{TIMEFRAME}.csv`
- Example: `C:/Users/YourName/AppData/Roaming/MetaTrader 5/Files/Data/BTCUSD-M1.csv`

**CSV Format (Bar Data):**
```csv
timestamp,open,high,low,close,tick_volume
1699900800,35234.50,35250.00,35200.00,35245.25,125
1699900860,35245.25,35260.00,35240.00,35255.00,98
```

**CSV Format (Tick Data):**
```csv
tick_time_ms,bid,ask
1699900800123,35234.50,35236.75
1699900800456,35235.00,35237.25
```

#### 4. TRADES - Get Historical Trades

Retrieve all historical trades/deals from your account.

**Request:**
```python
command = {
    "action": "HISTORY",
    "actionType": "TRADES"
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()

response = data_socket.recv_string()
data = json.loads(response)
```

**Response Format:**
```json
{
  "trades": [
    {
      "ticket": 123456789,
      "time": 1699900800,
      "price": 35234.50,
      "volume": 0.1,
      "symbol": "BTCUSD",
      "type": "Buy",
      "entry": 0,
      "profit": 45.50
    },
    ...
  ]
}
```

## Available Timeframes

| Code | Description | Bar Duration |
|------|-------------|--------------|
| `TICK` | Individual ticks | Variable (milliseconds) |
| `M1` | 1 Minute | 60 seconds |
| `M5` | 5 Minutes | 5 minutes |
| `M15` | 15 Minutes | 15 minutes |
| `M30` | 30 Minutes | 30 minutes |
| `H1` | 1 Hour | 1 hour |
| `H4` | 4 Hours | 4 hours |
| `D1` | 1 Day | 1 day |
| `W1` | 1 Week | 1 week |
| `MN1` | 1 Month | 1 month |

## Complete Example

```python
#!/usr/bin/env python3
import zmq
import json
import time
import datetime

def get_historical_data(symbol, timeframe, days_back=7):
    """Get historical bar data for a symbol"""
    context = zmq.Context()

    # Connect sockets
    system_socket = context.socket(zmq.REQ)
    system_socket.connect("tcp://localhost:2201")
    system_socket.setsockopt(zmq.RCVTIMEO, 5000)

    data_socket = context.socket(zmq.PULL)
    data_socket.connect("tcp://localhost:2202")
    data_socket.setsockopt(zmq.RCVTIMEO, 10000)

    # Calculate date range
    to_date = int(time.time())
    from_date = to_date - (days_back * 24 * 60 * 60)

    # Send request
    command = {
        "action": "HISTORY",
        "actionType": "DATA",
        "symbol": symbol,
        "chartTF": timeframe,
        "fromDate": from_date,
        "toDate": to_date
    }

    print(f"Requesting {days_back} days of {timeframe} data for {symbol}...")
    system_socket.send_string(json.dumps(command))
    ack = system_socket.recv_string()
    print(f"Server acknowledged: {ack}")

    # Receive data
    print("Waiting for data...")
    response = data_socket.recv_string()
    data = json.loads(response)

    # Process data
    if "data" in data and len(data["data"]) > 0:
        bars = data["data"]
        print(f"\nReceived {len(bars)} bars")
        print(f"First bar: {datetime.datetime.fromtimestamp(bars[0][0])}")
        print(f"Last bar:  {datetime.datetime.fromtimestamp(bars[-1][0])}")
        print(f"\nSample data (first 3 bars):")
        for i in range(min(3, len(bars))):
            bar = bars[i]
            dt = datetime.datetime.fromtimestamp(bar[0])
            print(f"  {dt} | O={bar[1]:.2f} H={bar[2]:.2f} L={bar[3]:.2f} C={bar[4]:.2f} V={bar[5]}")

        return bars
    else:
        print("No data received")
        return []

    # Cleanup
    system_socket.close()
    data_socket.close()
    context.term()

if __name__ == "__main__":
    # Get 7 days of M1 data for BTCUSD
    bars = get_historical_data("BTCUSD", "M1", days_back=7)

    # Get 1 hour of tick data
    # ticks = get_historical_data("BTCUSD", "TICK", days_back=1/24)
```

## Performance Considerations

1. **Large Data Sets**: Requesting many bars/ticks can take time and generate large responses
   - M1 data: ~1,440 bars per day
   - M5 data: ~288 bars per day
   - H1 data: ~24 bars per day
   - TICK data: Can be thousands per minute

2. **Socket Timeouts**: Increase timeout for large requests
   ```python
   data_socket.setsockopt(zmq.RCVTIMEO, 30000)  # 30 seconds
   ```

3. **JSON Response Size**: Very large responses (>1MB) may cause issues
   - Consider limiting date ranges
   - Use CSV export (`actionType="WRITE"`) for very large datasets

4. **Broker Limitations**: Some brokers limit historical data availability
   - Typically 1-3 months for tick data
   - Several years for bar data

## Error Handling

Common errors when requesting historical data:

| Error Code | Description | Solution |
|------------|-------------|----------|
| `ERR_MARKET_UNKNOWN_SYMBOL` | Symbol doesn't exist | Check symbol name spelling |
| `ERR_RETRIEVE_DATA_FAILED` | Failed to retrieve data | Check date range, broker connection |
| `ERR_CFILE_CREATION_FAILED` | Can't create CSV file | Check MT5 file permissions |

```python
try:
    response = data_socket.recv_string()
    data = json.loads(response)

    if data.get("error", False):
        print(f"Error: {data.get('description', 'Unknown error')}")
    else:
        # Process data
        pass
except zmq.Again:
    print("Timeout waiting for response")
except json.JSONDecodeError as e:
    print(f"JSON decode error: {e}")
```

## See Also

- [Live Data Guide](LIVE_DATA_GUIDE.md) - For real-time streaming data
- [Account Guide](ACCOUNT_GUIDE.md) - For account and position information
- [Trade Guide](TRADE_GUIDE.md) - For placing orders
