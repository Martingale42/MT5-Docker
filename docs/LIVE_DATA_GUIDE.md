# Getting Real-Time Tick Data (Bid/Ask Prices) from MT5

## Overview

MT5 JsonAPI supports **two types of live data streams**:

1. **Bar Data (M1, M5, H1, etc.)** - OHLCV bars that update when a bar closes
2. **Tick Data (TICK)** - Real-time bid/ask prices that update on every price change

## Data Formats

### Bar Data Format (M1, M5, H1, D1, etc.)

```json
{
  "status": "CONNECTED",
  "symbol": "BTCUSD",
  "timeframe": "M1",
  "data": [
    timestamp,      // Unix timestamp
    open,           // Bar open price
    high,           // Bar high price
    low,            // Bar low price
    close,          // Bar close price
    tick_volume     // Number of ticks in the bar
  ]
}
```

**Update Frequency**: Only when a bar closes (e.g., M1 = every 60 seconds, M5 = every 300 seconds)

### Tick Data Format (TICK)

```json
{
  "status": "CONNECTED",
  "symbol": "BTCUSD",
  "timeframe": "TICK",
  "data": [
    tick_time_ms,   // Unix timestamp in milliseconds
    bid,            // Current bid price
    ask             // Current ask price
  ]
}
```

**Update Frequency**: On **every price change** (typically multiple times per second during active trading)

## Usage

### Configure Symbol for Tick Data

To receive real-time tick updates, configure with `chartTF="TICK"`:

```python
import zmq
import json

# Connect to system socket
system_socket = context.socket(zmq.REQ)
system_socket.connect("tcp://localhost:2201")

# Configure for TICK data
command = {
    "action": "CONFIG",
    "actionType": "CONFIG",
    "symbol": "BTCUSD",
    "chartTF": "TICK"  # ← Key: Use "TICK" for real-time bid/ask
}
system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()  # Receive "OK"

# Now listen on the live socket (port 2203)
live_socket = context.socket(zmq.PULL)
live_socket.connect("tcp://localhost:2203")

while True:
    msg = live_socket.recv_string()
    data = json.loads(msg)

    tick_data = data['data']
    bid = tick_data[1]
    ask = tick_data[2]
    spread = ask - bid

    print(f"Bid: {bid:.2f}, Ask: {ask:.2f}, Spread: {spread:.2f}")
```

### Configure Symbol for Bar Data

To receive bar-based updates (M1, M5, etc.):

```python
command = {
    "action": "CONFIG",
    "actionType": "CONFIG",
    "symbol": "BTCUSD",
    "chartTF": "M1"  # ← Use standard timeframe codes
}
```

Available timeframes:
- `TICK` - Real-time ticks
- `M1`, `M5`, `M15`, `M30` - Minutes
- `H1`, `H4` - Hours
- `D1` - Daily
- `W1` - Weekly
- `MN1` - Monthly

## Test Scripts

### Quick Tick Stream Test

```bash
uv run scripts/check_tick_stream.py
```

This script:
- Configures BTCUSD for TICK data
- Listens for 30 seconds
- Shows real-time bid/ask updates with price change indicators (↑/↓)
- Reports ticks per second

### Full Test Suite

```bash
uv run scripts/test_jsonapi.py
```

This includes tests for:
1. Account info
2. Symbol configuration
3. Historical market data (OHLCV)
4. Live bar stream (M1)
5. **Real-time tick stream (bid/ask)** ← New!
6. Economic calendar

## Implementation Details

The MT5 side is implemented in `JsonAPI.mq5:199-275` (StreamPriceData function):

```mq5
if( chartTF == "TICK"){
  if(SymbolInfoTick(symbol,tick) !=true) { /*error processing */ };
  thisBar=(datetime) tick.time_msc;

  // Tick data format
  Data[0] = (long)    tick.time_msc;
  Data[1] = (double)  tick.bid;      // Real bid price
  Data[2] = (double)  tick.ask;      // Real ask price
}
else {
  // Bar data format (M1, M5, etc.)
  Data[0] = (long)    rates[0].time;
  Data[1] = (double)  rates[0].open;
  Data[2] = (double)  rates[0].high;
  Data[3] = (double)  rates[0].low;
  Data[4] = (double)  rates[0].close;
  Data[5] = (double)  rates[0].tick_volume;
}
```

## Performance Considerations

1. **Tick data generates much more traffic** than bar data:
   - Bar data: 1 update per bar close (e.g., M1 = 1/minute)
   - Tick data: Multiple updates per second during active trading

2. **Socket buffer settings** (JsonAPI.mq5:94):
   - `liveSocket.setSendHighWaterMark(1)` - Only keeps latest tick
   - Prevents memory buildup if client can't keep up

3. **Timeout settings** affect responsiveness:
   - Use shorter timeouts (e.g., 100-1000ms) for tick data
   - Use longer timeouts for bar data

## Troubleshooting

**No tick updates received?**
- Check if markets are open and active
- Verify symbol is configured correctly
- Ensure MT5 terminal is connected to broker
- Check if symbol requires subscription (some brokers)

**Getting N/A values?**
- You're using bar data format to parse tick data (or vice versa)
- Use correct data array structure based on `timeframe` field

**Too many updates?**
- Implement throttling on client side
- Use bar data (M1, M5) instead of TICK
- Filter updates based on minimum price change threshold
