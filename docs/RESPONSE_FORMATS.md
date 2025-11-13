# MT5-Docker JsonAPI Response Formats

**Generated:** 2025-11-10
**Purpose:** Document actual JSON response formats for Nautilus Trader integration

---

## Architecture Overview

### Request-Response Flow

```
Client                    MT5-Docker JsonAPI
  │                              │
  ├──(1) REQ Socket ────────────>│ sys_port (2201)
  │   Send: {"action": "ACCOUNT"}│
  │                              │
  │<─(2) REP Socket ─────────────┤
  │   Receive: "OK" (ACK)        │
  │                              │
  │<─(3) PULL Socket ────────────┤ data_port (2202)
  │   Receive: {actual data}     │
  └──────────────────────────────┘
```

**Key Points:**
1. Commands sent to `sys_port (2201)` via REQ socket
2. Immediate ACK received on same socket: `"OK"`
3. Actual data response received on `data_port (2202)` via PULL socket
4. Live streaming data on `live_port (2203)` via PULL socket
5. Trade confirmations on `stream_port (2204)` via PULL socket

---

## Port Usage Summary

| Port | Socket Type | Direction | Purpose |
|------|-------------|-----------|---------|
| 2201 | REQ/REP | Bidirectional | Send commands, receive "OK" ACK |
| 2202 | PUSH/PULL | Server→Client | Receive command response data |
| 2203 | PUSH/PULL | Server→Client | Receive live price streams (ticks/bars) |
| 2204 | PUSH/PULL | Server→Client | Receive trade confirmations |

---

## Response Formats by Action

### 1. ACCOUNT - Get Account Information

**Request (sys_port 2201):**
```json
{"action": "ACCOUNT"}
```

**ACK (sys_port 2201):**
```
"OK"
```

**Response (data_port 2202):**
```json
{
  "error": false,
  "broker": "OANDA Corporation",
  "currency": "USD",
  "server": "OANDA-Demo-1",
  "trading_allowed": 1,
  "bot_trading": 1,
  "balance": 10000.0,
  "equity": 10000.0,
  "margin": 0.0,
  "margin_free": 10000.0,
  "margin_level": 0.0
}
```

**Field Types:**
- `error`: boolean
- `broker`: string
- `currency`: string (3-letter code)
- `server`: string
- `trading_allowed`: int (0 or 1)
- `bot_trading`: int (0 or 1)
- `balance`: float
- `equity`: float
- `margin`: float
- `margin_free`: float
- `margin_level`: float (percentage)

---

### 2. BALANCE - Get Balance Only

**Request (sys_port 2201):**
```json
{"action": "BALANCE"}
```

**Response (data_port 2202):**
```json
{
  "balance": 10000.0,
  "equity": 10000.0,
  "margin": 0.0,
  "margin_free": 10000.0
}
```

**Field Types:**
- All fields: float

---

### 3. CONFIG - Subscribe to Symbol Data

**Request (sys_port 2201):**
```json
{
  "action": "CONFIG",
  "actionType": "CONFIG",
  "symbol": "XAUUSD.sml",
  "chartTF": "M1"
}
```

**Response (data_port 2202):**
```json
{
  "error": false,
  "lastError": "0",
  "description": "ERR_SUCCESS",
  "function": "ScriptConfiguration"
}
```

**Valid chartTF Values:**
- `"TICK"` - Real-time tick data (bid/ask)
- `"M1"` - 1-minute bars
- `"M5"` - 5-minute bars
- `"M15"` - 15-minute bars
- `"M30"` - 30-minute bars
- `"H1"` - 1-hour bars
- `"H4"` - 4-hour bars
- `"D1"` - Daily bars
- `"W1"` - Weekly bars
- `"MN1"` - Monthly bars

**After CONFIG:**
- Live data starts streaming on `live_port (2203)`
- Data continues until MT5 is restarted or symbol is reconfigured

---

### 4. HISTORY - Get Historical Bar Data

**Request (sys_port 2201):**
```json
{
  "action": "HISTORY",
  "actionType": "DATA",
  "symbol": "XAUUSD.sml",
  "chartTF": "M1",
  "fromDate": 1762159486,
  "toDate": 1762764286
}
```

**Response (data_port 2202):**
```json
{
  "data": [
    [1762159500, 4015.63, 4016.635, 4014.695, 4014.725, 216.0],
    [1762159560, 4014.695, 4015.465, 4014.055, 4014.575, 161.0],
    ...
  ],
  "symbol": "XAUUSD.sml",
  "timeframe": "M1"
}
```

**Bar Data Array Structure:**
```
[
  timestamp,     // Unix timestamp (seconds)
  open,          // Open price (float)
  high,          // High price (float)
  low,           // Low price (float)
  close,         // Close price (float)
  tick_volume    // Number of ticks (float)
]
```

---

### 5. HISTORY - Get Historical Tick Data

**Request (sys_port 2201):**
```json
{
  "action": "HISTORY",
  "actionType": "DATA",
  "symbol": "BTCUSD",
  "chartTF": "TICK",
  "fromDate": 1762760687,
  "toDate": 1762764287
}
```

**Response (data_port 2202):**
```json
{
  "data": [
    [1762760687192, 106104.6, 106150.77],
    [1762760687330, 106106.5, 106152.67],
    ...
  ],
  "symbol": "BTCUSD",
  "timeframe": "TICK"
}
```

**Tick Data Array Structure:**
```
[
  timestamp_ms,  // Unix timestamp in milliseconds
  bid,           // Bid price (float)
  ask            // Ask price (float)
]
```

---

### 6. POSITIONS - Get Open Positions

**Request (sys_port 2201):**
```json
{"action": "POSITIONS"}
```

**Response (data_port 2202) - Empty:**
```json
{
  "positions": []
}
```

**Response (data_port 2202) - With Positions:**
```json
{
  "error": false,
  "server_time": 1699900800,
  "positions": [
    {
      "id": 123456789,
      "magic": 0,
      "symbol": "BTCUSD",
      "type": "POSITION_TYPE_BUY",
      "time_setup": 1699900500,
      "open": 35234.50,
      "stoploss": 35100.00,
      "takeprofit": 35500.00,
      "volume": 0.1
    }
  ]
}
```

---

### 7. ORDERS - Get Pending Orders

**Request (sys_port 2201):**
```json
{"action": "ORDERS"}
```

**Response (data_port 2202) - Empty:**
```json
{
  "error": false,
  "orders": []
}
```

**Response (data_port 2202) - With Orders:**
```json
{
  "error": false,
  "orders": [
    {
      "id": "987654321",
      "magic": 0,
      "symbol": "BTCUSD",
      "type": "ORDER_TYPE_BUY_LIMIT",
      "time_setup": 1699900700,
      "open": 35000.00,
      "stoploss": 34900.00,
      "takeprofit": 35200.00,
      "volume": 0.1
    }
  ]
}
```

---

### 8. TRADE - Submit Order

**Request (sys_port 2201):**
```json
{
  "action": "TRADE",
  "actionType": "ORDER_TYPE_BUY",
  "symbol": "BTCUSD",
  "volume": 0.01,
  "stoploss": 0,
  "takeprofit": 0,
  "deviation": 10,
  "comment": "Test order"
}
```

**Response (data_port 2202):**
```json
{
  "error": false,
  "retcode": 10009,
  "desription": "TRADE_RETCODE_DONE",
  "order": 30943837,
  "volume": 0.01,
  "price": 105963.33,
  "bid": 105916.8,
  "ask": 105963.33,
  "function": "TradingModule"
}
```

**Trade Confirmation (stream_port 2204):**
```json
{
  "request": {
    "action": "TRADE_ACTION_DEAL",
    "order": 30943837,
    "symbol": "BTCUSD",
    "volume": 0.01,
    "price": 0.0,
    "stoplimit": 0.0,
    "sl": 0.0,
    "tp": 0.0,
    "deviation": 10,
    "type": "ORDER_TYPE_BUY",
    "type_filling": "ORDER_FILLING_IOC",
    "type_time": "ORDER_TIME_GTC",
    "expiration": 0,
    "comment": "Test order",
    "position": 0,
    "position_by": 0
  },
  "result": {
    "retcode": 10009,
    "result": "TRADE_RETCODE_DONE",
    "deal": 30943837,
    "order": 30943837,
    "volume": 0.01,
    "price": 105963.33,
    "comment": null,
    "request_id": -1909797175,
    "retcode_external": 0
  }
}
```

**Return Codes:**
- `10009` - TRADE_RETCODE_DONE (Success)
- `10004` - TRADE_RETCODE_REQUOTE (Requote)
- `10006` - TRADE_RETCODE_REJECT (Rejected)
- `10007` - TRADE_RETCODE_CANCEL (Canceled)
- `10008` - TRADE_RETCODE_PLACED (Order placed)
- `10013` - TRADE_RETCODE_INVALID (Invalid request)
- `10014` - TRADE_RETCODE_INVALID_VOLUME
- `10015` - TRADE_RETCODE_INVALID_PRICE
- `10016` - TRADE_RETCODE_INVALID_STOPS
- `10018` - TRADE_RETCODE_MARKET_CLOSED
- `10019` - TRADE_RETCODE_NO_MONEY
- `10025` - TRADE_RETCODE_LOCKED

---

### 9. INSTRUMENTS - NOT SUPPORTED ⚠️

**Request (sys_port 2201):**
```json
{"action": "INSTRUMENTS"}
```

**Response (data_port 2202):**
```json
{
  "error": true,
  "lastError": "65538",
  "description": "ERR_WRONG_ACTION",
  "function": "RequestHandler"
}
```

**⚠️ CRITICAL:** MT5-Docker JsonAPI does **NOT** support the INSTRUMENTS action!

**Workaround for Nautilus Integration:**
- Maintain a static list of instruments based on broker
- Or load instruments from config file
- Or query symbols from MT5 terminal using a different method

---

## Live Streaming Formats

### Tick Stream (live_port 2203) - After CONFIG with chartTF="TICK"

```json
{
  "status": "CONNECTED",
  "symbol": "BTCUSD",
  "timeframe": "TICK",
  "data": [
    1762771485192,  // timestamp_ms
    105907.7,       // bid
    105953.92       // ask
  ]
}
```

**Update Frequency:** Multiple times per second during active trading

---

### Bar Stream (live_port 2203) - After CONFIG with chartTF="M1"

```json
{
  "status": "CONNECTED",
  "symbol": "XAUUSD.sml",
  "timeframe": "M1",
  "data": [
    1762771440,    // timestamp (seconds)
    4015.63,       // open
    4016.635,      // high
    4014.695,      // low
    4014.725,      // close
    216.0          // tick_volume
  ]
}
```

**Update Frequency:**
- M1: Every 60 seconds (when minute closes)
- M5: Every 300 seconds
- H1: Every 3600 seconds
- etc.

---

## Error Response Format

All errors follow this structure:

```json
{
  "error": true,
  "lastError": "error_code",
  "description": "ERR_DESCRIPTION",
  "function": "FunctionName"
}
```

**Common Error Codes:**
- `65538` - ERR_WRONG_ACTION
- `0` - ERR_SUCCESS (not an error)

---

## Implementation Notes for Nautilus Trader

### 1. Request-Response Pattern

```python
# Send command to sys_port (REQ socket)
sys_socket.send_string(json.dumps({"action": "ACCOUNT"}))

# Get ACK
ack = sys_socket.recv_string()  # Returns "OK"

# Get actual data from data_port (PULL socket)
response = data_socket.recv_string()
data = json.loads(response)
```

### 2. Instrument Loading Workaround

Since INSTRUMENTS is not supported, use one of:

**Option A: Config File**
```python
instruments = ["EURUSD", "GBPUSD", "XAUUSD.sml", "BTCUSD"]
```

**Option B: Dynamic Discovery (requires custom MQL5 script)**
- Modify JsonAPI.mq5 to add INSTRUMENTS support
- Or use SymbolsTotal() + SymbolName() in MQL5

**Option C: Broker-Specific Lists**
```python
OANDA_INSTRUMENTS = ["EURUSD", "GBPUSD", ...]
EXNESS_INSTRUMENTS = [...]
```

### 3. Timeouts

- **sys_socket (REQ)**: 5 seconds
- **data_socket (PULL)**: 10 seconds (larger responses like HISTORY)
- **live_socket (PULL)**: 1-5 seconds
- **stream_socket (PULL)**: 1-5 seconds

### 4. Response Sizes

- ACCOUNT: ~200 bytes
- BALANCE: ~90 bytes
- CONFIG: ~90 bytes
- POSITIONS/ORDERS: ~20-1000 bytes (depends on count)
- HISTORY bars (7 days M1): ~460KB (6870 bars)
- HISTORY ticks (1 hour): ~200KB (4873 ticks)
- TRADE: ~180 bytes
- Live tick: ~100 bytes per message
- Live M1 bar: ~120 bytes per message

---

## Testing Checklist

- [x] ACCOUNT response captured
- [x] BALANCE response captured
- [x] CONFIG response captured
- [x] HISTORY bars response captured
- [x] HISTORY ticks response captured
- [x] POSITIONS response captured
- [x] ORDERS response captured
- [x] TRADE execution captured
- [x] Trade confirmation (stream_port) captured
- [x] Live tick data captured
- [ ] Live M1 bar data captured (needs 70s capture window)
- [x] Instrument loading limitation documented

---

## Captured Response Samples

All sample responses saved to: `MT5-Docker/data/response_samples/`

Files:
- `account.json`
- `balance.json`
- `config_m1.json`
- `config_tick.json`
- `history_bars.json`
- `history_ticks.json`
- `positions.json`
- `orders.json`
- `trade_buy.json`
- `trade_confirmation.json`
- `live_stream_tick.json`
- `live_stream_m1.json` (contains tick data, needs re-capture)
- `instruments.json` (error response)

---

## Next Steps for Implementation

1. ✅ Understand MT5-Docker response formats
2. ⚠️ Design workaround for missing INSTRUMENTS action
3. 🔧 Implement data_port (2202) support in Rust client
4. 🔧 Update request-response pattern to use data_port
5. 🔧 Implement response parsers for each action type
6. 🧪 Test with live MT5-Docker instance
