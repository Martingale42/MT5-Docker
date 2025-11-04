# Account, Balance & Position API Guide

## Overview

MT5 JsonAPI provides APIs to query account information, balances, open positions, and pending orders. These endpoints are read-only and do not modify any account state.

## Available Commands

| Command | Description |
|---------|-------------|
| `ACCOUNT` | Get full account information |
| `BALANCE` | Get balance and margin info only |
| `POSITIONS` | Get all open positions |
| `ORDERS` | Get all pending orders |

---

## 1. ACCOUNT - Get Account Information

Retrieves comprehensive account information including broker details, balance, equity, and margin.

### Request

```python
import zmq
import json

context = zmq.Context()

# System socket
system_socket = context.socket(zmq.REQ)
system_socket.connect("tcp://localhost:2201")

# Data socket
data_socket = context.socket(zmq.PULL)
data_socket.connect("tcp://localhost:2202")

# Request account info
command = {"action": "ACCOUNT"}
system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()  # "OK"

# Receive response
response = data_socket.recv_string()
account_info = json.loads(response)
print(account_info)
```

### Response Format

```json
{
  "error": false,
  "broker": "OANDA Corporation",
  "currency": "USD",
  "server": "OANDA-Demo-1",
  "trading_allowed": 1,
  "bot_trading": 1,
  "balance": 10000.0,
  "equity": 10250.50,
  "margin": 500.0,
  "margin_free": 9750.50,
  "margin_level": 2050.1
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `error` | bool | false if successful |
| `broker` | string | Broker company name |
| `currency` | string | Account currency (USD, EUR, etc.) |
| `server` | string | Trading server name |
| `trading_allowed` | int | 1 if trading is allowed in terminal |
| `bot_trading` | int | 1 if Expert Advisors/bots are allowed |
| `balance` | float | Account balance |
| `equity` | float | Current equity (balance + floating P/L) |
| `margin` | float | Margin used by open positions |
| `margin_free` | float | Free margin available |
| `margin_level` | float | Margin level percentage |

---

## 2. BALANCE - Get Balance Information

Retrieves only balance and margin information (lighter than ACCOUNT).

### Request

```python
command = {"action": "BALANCE"}
system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()

response = data_socket.recv_string()
balance_info = json.loads(response)
```

### Response Format

```json
{
  "balance": 10000.0,
  "equity": 10250.50,
  "margin": 500.0,
  "margin_free": 9750.50
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `balance` | float | Account balance |
| `equity` | float | Current equity (balance + floating P/L) |
| `margin` | float | Margin used by open positions |
| `margin_free` | float | Free margin available |

**Use Cases:**
- Quick balance checks in trading loops
- Monitoring account status without full account details
- Lightweight alternative to ACCOUNT command

---

## 3. POSITIONS - Get Open Positions

Retrieves all currently open positions.

### Request

```python
command = {"action": "POSITIONS"}
system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()

response = data_socket.recv_string()
positions = json.loads(response)
```

### Response Format

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
    },
    {
      "id": 123456790,
      "magic": 12345,
      "symbol": "XAUUSD.sml",
      "type": "POSITION_TYPE_SELL",
      "time_setup": 1699900600,
      "open": 1985.50,
      "stoploss": 1990.00,
      "takeprofit": 1975.00,
      "volume": 0.5
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `error` | bool | false if successful |
| `server_time` | int | Current server time (Unix timestamp) |
| `positions` | array | Array of position objects |

### Position Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Position identifier (unique) |
| `magic` | int | Magic number (for EA identification) |
| `symbol` | string | Trading symbol |
| `type` | string | Position type: `POSITION_TYPE_BUY` or `POSITION_TYPE_SELL` |
| `time_setup` | int | Position open time (Unix timestamp) |
| `open` | float | Position open price |
| `stoploss` | float | Stop loss price (0 if not set) |
| `takeprofit` | float | Take profit price (0 if not set) |
| `volume` | float | Position volume (lot size) |

**Note:** If no positions are open, `positions` will be an empty array: `[]`

---

## 4. ORDERS - Get Pending Orders

Retrieves all pending orders (limit, stop orders that haven't executed yet).

### Request

```python
command = {"action": "ORDERS"}
system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()

response = data_socket.recv_string()
orders = json.loads(response)
```

### Response Format

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
    },
    {
      "id": "987654322",
      "magic": 12345,
      "symbol": "EURUSD",
      "type": "ORDER_TYPE_SELL_STOP",
      "time_setup": 1699900800,
      "open": 1.0850,
      "stoploss": 1.0870,
      "takeprofit": 1.0820,
      "volume": 1.0
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `error` | bool | false if successful |
| `orders` | array | Array of order objects |

### Order Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Order ticket number |
| `magic` | int | Magic number (for EA identification) |
| `symbol` | string | Trading symbol |
| `type` | string | Order type (see table below) |
| `time_setup` | int | Order placement time (Unix timestamp) |
| `open` | float | Order price (entry price) |
| `stoploss` | float | Stop loss price (0 if not set) |
| `takeprofit` | float | Take profit price (0 if not set) |
| `volume` | float | Order volume (lot size) |

### Order Types

| Type | Description |
|------|-------------|
| `ORDER_TYPE_BUY_LIMIT` | Buy limit order (buy when price drops to this level) |
| `ORDER_TYPE_SELL_LIMIT` | Sell limit order (sell when price rises to this level) |
| `ORDER_TYPE_BUY_STOP` | Buy stop order (buy when price rises to this level) |
| `ORDER_TYPE_SELL_STOP` | Sell stop order (sell when price drops to this level) |

**Note:** If no pending orders exist, `orders` will be an empty array: `[]`

---

## Complete Example: Account Monitor

```python
#!/usr/bin/env python3
"""
Account monitoring script - displays account info, positions, and orders
"""
import zmq
import json
import time
from datetime import datetime

class MT5AccountMonitor:
    def __init__(self, host="localhost"):
        self.context = zmq.Context()

        self.system_socket = self.context.socket(zmq.REQ)
        self.system_socket.connect(f"tcp://{host}:2201")
        self.system_socket.setsockopt(zmq.RCVTIMEO, 5000)

        self.data_socket = self.context.socket(zmq.PULL)
        self.data_socket.connect(f"tcp://{host}:2202")
        self.data_socket.setsockopt(zmq.RCVTIMEO, 5000)

    def send_command(self, command):
        """Send command and get response"""
        self.system_socket.send_string(json.dumps(command))
        ack = self.system_socket.recv_string()

        response = self.data_socket.recv_string()
        return json.loads(response)

    def get_account_info(self):
        """Get full account information"""
        return self.send_command({"action": "ACCOUNT"})

    def get_balance(self):
        """Get balance information"""
        return self.send_command({"action": "BALANCE"})

    def get_positions(self):
        """Get open positions"""
        return self.send_command({"action": "POSITIONS"})

    def get_orders(self):
        """Get pending orders"""
        return self.send_command({"action": "ORDERS"})

    def display_account_summary(self):
        """Display comprehensive account summary"""
        print("=" * 70)
        print("ACCOUNT SUMMARY")
        print("=" * 70)

        # Account info
        account = self.get_account_info()
        print(f"\nBroker: {account['broker']}")
        print(f"Server: {account['server']}")
        print(f"Currency: {account['currency']}")
        print(f"Trading Allowed: {'Yes' if account['trading_allowed'] else 'No'}")
        print(f"Bot Trading: {'Yes' if account['bot_trading'] else 'No'}")

        print(f"\nBalance: ${account['balance']:,.2f}")
        print(f"Equity: ${account['equity']:,.2f}")
        print(f"P/L: ${account['equity'] - account['balance']:,.2f}")
        print(f"Margin Used: ${account['margin']:,.2f}")
        print(f"Margin Free: ${account['margin_free']:,.2f}")
        if account['margin'] > 0:
            print(f"Margin Level: {account['margin_level']:.2f}%")

        # Open positions
        positions = self.get_positions()
        print(f"\n{'OPEN POSITIONS':-^70}")
        if positions.get('positions') and len(positions['positions']) > 0:
            for pos in positions['positions']:
                pos_type = "BUY" if "BUY" in pos['type'] else "SELL"
                open_time = datetime.fromtimestamp(pos['time_setup'])
                print(f"\n  ID: {pos['id']}")
                print(f"  Symbol: {pos['symbol']}")
                print(f"  Type: {pos_type}")
                print(f"  Volume: {pos['volume']}")
                print(f"  Open Price: {pos['open']:.5f}")
                print(f"  SL: {pos['stoploss']:.5f}" if pos['stoploss'] > 0 else "  SL: Not set")
                print(f"  TP: {pos['takeprofit']:.5f}" if pos['takeprofit'] > 0 else "  TP: Not set")
                print(f"  Opened: {open_time}")
        else:
            print("  No open positions")

        # Pending orders
        orders = self.get_orders()
        print(f"\n{'PENDING ORDERS':-^70}")
        if orders.get('orders') and len(orders['orders']) > 0:
            for order in orders['orders']:
                order_time = datetime.fromtimestamp(order['time_setup'])
                print(f"\n  ID: {order['id']}")
                print(f"  Symbol: {order['symbol']}")
                print(f"  Type: {order['type'].replace('ORDER_TYPE_', '')}")
                print(f"  Volume: {order['volume']}")
                print(f"  Entry Price: {order['open']:.5f}")
                print(f"  SL: {order['stoploss']:.5f}" if order['stoploss'] > 0 else "  SL: Not set")
                print(f"  TP: {order['takeprofit']:.5f}" if order['takeprofit'] > 0 else "  TP: Not set")
                print(f"  Placed: {order_time}")
        else:
            print("  No pending orders")

        print("=" * 70)

    def close(self):
        """Close connections"""
        self.system_socket.close()
        self.data_socket.close()
        self.context.term()

if __name__ == "__main__":
    monitor = MT5AccountMonitor()

    try:
        monitor.display_account_summary()
    finally:
        monitor.close()
```

## Error Handling

```python
try:
    response = data_socket.recv_string()
    data = json.loads(response)

    if data.get("error", False):
        print(f"Error retrieving data: {data.get('description', 'Unknown error')}")
    else:
        # Process data
        pass

except zmq.Again:
    print("Timeout waiting for response")
except json.JSONDecodeError as e:
    print(f"JSON decode error: {e}")
```

## Common Use Cases

### 1. Check Account Health Before Trading

```python
balance = monitor.get_balance()
if balance['margin_free'] < 1000:
    print("Warning: Low free margin!")
    # Don't place new trades
```

### 2. Monitor Position P/L

```python
account = monitor.get_account_info()
floating_pl = account['equity'] - account['balance']
print(f"Current P/L: ${floating_pl:,.2f}")
```

### 3. Count Open Positions by Symbol

```python
positions = monitor.get_positions()
symbol_counts = {}
for pos in positions.get('positions', []):
    symbol = pos['symbol']
    symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1

print("Positions per symbol:", symbol_counts)
```

### 4. Find Positions Without Stop Loss

```python
positions = monitor.get_positions()
for pos in positions.get('positions', []):
    if pos['stoploss'] == 0:
        print(f"Warning: Position {pos['id']} on {pos['symbol']} has no stop loss!")
```

## See Also

- [Trade Guide](TRADE_GUIDE.md) - For placing and managing orders
- [Historical Data Guide](HIST_DATA_GUIDE.md) - For market data
- [Live Data Guide](LIVE_DATA_GUIDE.md) - For real-time streaming
