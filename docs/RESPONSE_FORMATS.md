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

**⚠️ DEPRECATED:** MT5-Docker JsonAPI does **NOT** support the INSTRUMENTS action!

Use **SYMBOL_INFO** instead (see section 10 below).

---

### 10. SYMBOL_INFO - Get Symbol Specifications ✅

**Purpose:** Query detailed symbol specifications from MT5 using SymbolInfo* functions. This provides all necessary information to create proper instrument definitions (price precision, lot sizes, margins, etc.).

#### Request Format (sys_port 2201):

**Option 1: Single Symbol**
```json
{
  "action": "SYMBOL_INFO",
  "symbol": "EURAUD"
}
```

**Option 2: Multiple Symbols**
```json
{
  "action": "SYMBOL_INFO",
  "symbols": ["EURAUD", "EURUSD", "BTCUSD"]
}
```

**Option 3: All Symbols** (no symbol specified)
```json
{
  "action": "SYMBOL_INFO"
}
```

#### Response Format (data_port 2202):

```json
{
  "error": false,
  "symbols": [
    {
      "symbol": "EURAUD",
      "description": "Euro vs Australian Dollar",
      "base_currency": "EUR",
      "quote_currency": "AUD",
      "profit_currency": "AUD",
      "margin_currency": "EUR",

      "digits": "5",
      "point": "0.00001000",
      "spread": "15",
      "stops_level": "0",

      "contract_size": "100000.00000",
      "tick_value": "0.66666000",
      "tick_size": "0.00001000",

      "volume_min": "0.01000",
      "volume_max": "500.00000",
      "volume_step": "0.01000",
      "volume_limit": "0.00000",

      "swap_long": "-0.59000",
      "swap_short": "0.05000",
      "swap_mode": "0",

      "trade_mode": "0",
      "trade_execution": "2",
      "trade_calc_mode": "0",

      "expiration_mode": "15",
      "filling_mode": "2",
      "order_mode": "55",

      "margin_initial": "0.00000",
      "margin_maintenance": "0.00000",
      "margin_hedged": "0.00000",

      "select": "true",
      "visible": "true",

      "session_deals": "0",
      "session_buy_orders": "0",
      "session_sell_orders": "0",

      "time": "1763050461",
      "bid": "1.62345000",
      "bidlow": "1.62100000",
      "bidhigh": "1.62500000",
      "ask": "1.62360000",
      "asklow": "1.62115000",
      "askhigh": "1.62515000",
      "last": "0.00000000",

      "trade_tick_value_profit": "0.66666000",
      "trade_tick_value_loss": "0.66666988",
      "trade_freeze_level": "0"
    }
  ]
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Symbol name (e.g., "EURAUD") |
| `description` | string | Human-readable description |
| `base_currency` | string | Base currency code (ISO 4217) |
| `quote_currency` | string | Quote currency code |
| `digits` | string | Price decimal places (5 for most forex) |
| `point` | string | Minimum price change (0.00001 for 5-digit) |
| `contract_size` | string | Standard lot size (100000 for forex) |
| `tick_size` | string | Minimum price change |
| `tick_value` | string | Value of 1 tick in account currency |
| `volume_min` | string | Minimum order size (0.01 = micro lot) |
| `volume_max` | string | Maximum order size |
| `volume_step` | string | Order size increment |
| `trade_mode` | string | 0=Full, 4=CloseOnly |
| `trade_execution` | string | 0=Request, 1=Instant, 2=Market |
| `filling_mode` | string | Order filling modes bitmap |

**Note:** All numeric values are returned as strings because MQL5's CJAVal library requires string assignments.

#### Use Cases:

1. **Instrument Loading**: Query all symbols on startup to populate instrument definitions
2. **Dynamic Updates**: Query specific symbols when needed
3. **Broker Portability**: Works with any broker's symbol names (EURAUD, EURUSD, XAUUSD.sml, BTCUSD, etc.)

#### Example Integration (Nautilus Trader):

```python
# Request all instruments
sys_socket.send_string(json.dumps({"action": "SYMBOL_INFO"}))
ack = sys_socket.recv_string()  # "OK"

# Receive full response on data_port
response = data_socket.recv_string()
data = json.loads(response)

for symbol_info in data["symbols"]:
    # Create CurrencyPair instrument with proper specifications
    instrument = create_instrument_from_mt5(symbol_info)
```

---

## 11. CALENDAR - Economic Calendar Events

### Request Format

**All currencies:**
```json
{
  "action": "CALENDAR",
  "actionType": "DATA",
  "fromDate": 1731484800,
  "toDate": 1731571200
}
```

**Specific symbol (filters by symbol's base and quote currencies):**
```json
{
  "action": "CALENDAR",
  "actionType": "DATA",
  "symbol": "EURUSD",
  "fromDate": 1731484800,
  "toDate": 1731571200
}
```

**Parameters:**
- `action`: "CALENDAR"
- `actionType`: "DATA"
- `symbol`: (optional) Symbol name - filters events by related currencies (base and quote)
- `fromDate`: Unix timestamp in seconds (required)
- `toDate`: Unix timestamp in seconds (optional, defaults to current time)

### Response Format

```json
{
  "data": [
    [
      "2025.11.06 14:30",
      "USD",
      "1",
      "Challenger Job Cuts(challenger-job-cuts)",
      "United States(US)",
      "153.074 K",
      null,
      "54.064 K"
    ],
    [
      "2025.11.07 15:30",
      "USD",
      "3",
      "Nonfarm Payrolls(nonfarm-payrolls)",
      "United States(US)",
      null,
      null,
      null
    ]
  ]
}
```

**Array Structure:**

Each event is an array with 8 elements:

| Index | Field | Type | Description | Example |
|-------|-------|------|-------------|---------|
| 0 | datetime | string | Event date/time | "2025.11.06 14:30" |
| 1 | currency | string | Currency code | "USD", "EUR", "GBP" |
| 2 | importance | string | Importance level (0-3) | "0" (holiday), "1" (low), "2" (medium), "3" (high) |
| 3 | event_name | string | Name with slug in parentheses | "Nonfarm Payrolls(nonfarm-payrolls)" |
| 4 | country | string | Country name with code | "United States(US)" |
| 5 | actual | string or null | Actual released value | "153.074 K", "$13.09 B", null |
| 6 | forecast | string or null | Forecasted value | "4.2", null |
| 7 | previous | string or null | Previous value | "54.064 K", null |

**Notes:**
- DateTime format: "YYYY.MM.DD HH:MM" (24-hour format)
- Importance: "0" = holiday, "1" = low impact, "2" = medium impact, "3" = high impact
- Values can be null if not yet available or not applicable
- Values include units (e.g., "K" for thousands, "B" for billions, "%" for percentages)
- Event names include a slug identifier in parentheses
- When symbol is specified, only events for that symbol's base and quote currencies are returned
- Response contains duplicate events (MT5 calendar behavior)

### Use Cases

1. **Filter high-impact events for risk management**
   ```python
   # Get high-impact events (importance = "3")
   high_impact = [event for event in calendar_data["data"] if event[2] == "3"]
   ```

2. **Parse event datetime**
   ```python
   from datetime import datetime
   dt_str = event[0]  # "2025.11.06 14:30"
   dt = datetime.strptime(dt_str, "%Y.%m.%d %H:%M")
   ```

3. **Check for upcoming NFP (Non-Farm Payrolls)**
   ```python
   nfp_events = [e for e in data["data"] if "Nonfarm Payrolls" in e[3]]
   ```

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

### 2. Instrument Loading

Use the **SYMBOL_INFO** action to load instrument specifications:

```python
# Request all instruments
sys_socket.send_string(json.dumps({"action": "SYMBOL_INFO"}))
ack = sys_socket.recv_string()  # "OK"
response = data_socket.recv_string()
data = json.loads(response)

# data["symbols"] contains list of all symbol specifications
for symbol_info in data["symbols"]:
    # Create Nautilus Instrument from symbol_info
    # See section 10 for complete field list
    pass
```

**Alternative: Request specific symbols**
```python
# Single symbol
{"action": "SYMBOL_INFO", "symbol": "EURUSD"}

# Multiple symbols
{"action": "SYMBOL_INFO", "symbols": ["EURUSD", "GBPUSD", "BTCUSD"]}
```

**Note**: The deprecated INSTRUMENTS action is not supported and returns ERR_WRONG_ACTION.

### 3. Timeouts

- **sys_socket (REQ)**: 5 seconds
- **data_socket (PULL)**: 10 seconds (larger responses like HISTORY)
- **live_socket (PULL)**: 1-5 seconds
- **stream_socket (PULL)**: 1-5 seconds

### 4. Response Sizes

- ACCOUNT: ~200 bytes
- BALANCE: ~90 bytes
- CONFIG: ~90 bytes
- SYMBOL_INFO (single): ~1-2KB per symbol
- SYMBOL_INFO (all): ~10-50KB (depends on broker symbol count)
- CALENDAR (7 days): ~40-100KB (depends on number of events)
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
- [x] SYMBOL_INFO response captured (single, multiple, all symbols)
- [x] CALENDAR response captured (all currencies, specific symbol)
- [x] HISTORY bars response captured
- [x] HISTORY ticks response captured
- [x] POSITIONS response captured
- [x] ORDERS response captured
- [x] TRADE execution captured
- [x] Trade confirmation (stream_port) captured
- [x] Live tick data captured
- [ ] Live M1 bar data captured (needs 70s capture window)
- [x] Instrument loading implemented via SYMBOL_INFO

---

## Captured Response Samples

All sample responses saved to: `MT5-Docker/data/response_samples/`

Files:
- `account.json`
- `balance.json`
- `config_m1.json`
- `config_tick.json`
- `symbol_info_single.json` - Single symbol specifications
- `symbol_info_multiple.json` - Multiple symbol specifications
- `symbol_info_all.json` - All available symbols
- `calendar_all.json` - Economic calendar events (all currencies)
- `calendar_symbol.json` - Economic calendar events (specific symbol)
- `history_bars.json`
- `history_ticks.json`
- `positions.json`
- `orders.json`
- `trade_buy.json`
- `trade_confirmation.json`
- `live_stream_tick.json`
- `live_stream_m1.json` (contains tick data, needs re-capture)

---

## Implementation Status

1. ✅ Understand MT5-Docker response formats
2. ✅ Implement SYMBOL_INFO action in JsonAPI.mq5
3. ✅ Implement data_port (2202) support in Rust client
4. ✅ Update request-response pattern to use data_port
5. ✅ Implement response parsers for SYMBOL_INFO and other action types
6. ✅ Test with live MT5-Docker instance
7. ✅ End-to-end integration test (8/10 instruments loaded successfully)

**Result**: Nautilus Trader MT5 adapter now successfully loads instruments from MT5-Docker using the SYMBOL_INFO action.
