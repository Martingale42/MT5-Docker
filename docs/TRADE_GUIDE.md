# Trading & Order Execution API Guide

## Overview

MT5 JsonAPI provides comprehensive trading capabilities including market orders, pending orders, position management, and order modifications. All trading operations use the `TRADE` action with different `actionType` parameters.

## Command: TRADE

All trading operations use this command structure:

```python
{
    "action": "TRADE",
    "actionType": "<ORDER_TYPE>",
    "symbol": "BTCUSD",
    "volume": 0.1,
    "price": 35000.00,        # For pending orders
    "stoploss": 34900.00,     # Optional
    "takeprofit": 35200.00,   # Optional
    "deviation": 10,          # Max price deviation in points
    "comment": "My trade",    # Optional
    "expiration": 1699900800, # Unix timestamp, for pending orders
    "id": 123456789           # For modifications/closures
}
```

---

## Market Orders

### 1. BUY Market Order

Open a buy position at current market price (ASK price).

**Request:**
```python
import zmq
import json

context = zmq.Context()

# System socket
system_socket = context.socket(zmq.REQ)
system_socket.connect("tcp://localhost:2201")

# Stream socket (for trade confirmations)
stream_socket = context.socket(zmq.PULL)
stream_socket.connect("tcp://localhost:2204")
stream_socket.setsockopt(zmq.RCVTIMEO, 5000)

command = {
    "action": "TRADE",
    "actionType": "ORDER_TYPE_BUY",
    "symbol": "BTCUSD",
    "volume": 0.1,
    "stoploss": 34900.00,     # Optional
    "takeprofit": 35500.00,   # Optional
    "deviation": 10,
    "comment": "Buy BTCUSD"
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()  # "OK"

# Wait for trade confirmation on stream socket
confirmation = stream_socket.recv_string()
result = json.loads(confirmation)
print(result)
```

**Response (Stream Socket):**
```json
{
  "request": {
    "action": "TRADE_ACTION_DEAL",
    "order": 0,
    "symbol": "BTCUSD",
    "volume": 0.1,
    "price": 35234.50,
    "stoplimit": 0.0,
    "sl": 34900.0,
    "tp": 35500.0,
    "deviation": 10,
    "type": "ORDER_TYPE_BUY",
    "type_filling": "ORDER_FILLING_FOK",
    "type_time": "ORDER_TIME_GTC",
    "expiration": 0,
    "comment": "Buy BTCUSD",
    "position": 0,
    "position_by": 0
  },
  "result": {
    "retcode": 10009,
    "result": "TRADE_RETCODE_DONE",
    "deal": 123456789,
    "order": 123456789,
    "volume": 0.1,
    "price": 35234.50,
    "comment": "Request executed",
    "request_id": 0,
    "retcode_external": 0
  }
}
```

### 2. SELL Market Order

Open a sell position at current market price (BID price).

**Request:**
```python
command = {
    "action": "TRADE",
    "actionType": "ORDER_TYPE_SELL",
    "symbol": "BTCUSD",
    "volume": 0.1,
    "stoploss": 35600.00,
    "takeprofit": 34800.00,
    "deviation": 10,
    "comment": "Sell BTCUSD"
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()

confirmation = stream_socket.recv_string()
result = json.loads(confirmation)
```

---

## Pending Orders

Pending orders are placed at a specific price and execute when that price is reached.

### 3. BUY LIMIT Order

Buy when price drops to a specified level (below current ASK).

**Request:**
```python
command = {
    "action": "TRADE",
    "actionType": "ORDER_TYPE_BUY_LIMIT",
    "symbol": "BTCUSD",
    "volume": 0.1,
    "price": 35000.00,        # Entry price
    "stoploss": 34900.00,
    "takeprofit": 35200.00,
    "expiration": 1699900800, # Optional: order expires at this time
    "comment": "Buy limit order"
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()

confirmation = stream_socket.recv_string()
result = json.loads(confirmation)
```

**Use Case:** Buy when price dips to a better level.

### 4. SELL LIMIT Order

Sell when price rises to a specified level (above current BID).

**Request:**
```python
command = {
    "action": "TRADE",
    "actionType": "ORDER_TYPE_SELL_LIMIT",
    "symbol": "BTCUSD",
    "volume": 0.1,
    "price": 35500.00,
    "stoploss": 35600.00,
    "takeprofit": 35300.00,
    "comment": "Sell limit order"
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()

confirmation = stream_socket.recv_string()
result = json.loads(confirmation)
```

**Use Case:** Sell when price rises to a better level.

### 5. BUY STOP Order

Buy when price rises above a specified level (above current ASK) - breakout entry.

**Request:**
```python
command = {
    "action": "TRADE",
    "actionType": "ORDER_TYPE_BUY_STOP",
    "symbol": "BTCUSD",
    "volume": 0.1,
    "price": 35500.00,        # Trigger price
    "stoploss": 35400.00,
    "takeprofit": 35700.00,
    "comment": "Buy stop order"
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()

confirmation = stream_socket.recv_string()
result = json.loads(confirmation)
```

**Use Case:** Enter buy position on breakout above resistance.

### 6. SELL STOP Order

Sell when price drops below a specified level (below current BID) - breakdown entry.

**Request:**
```python
command = {
    "action": "TRADE",
    "actionType": "ORDER_TYPE_SELL_STOP",
    "symbol": "BTCUSD",
    "volume": 0.1,
    "price": 34800.00,
    "stoploss": 34900.00,
    "takeprofit": 34600.00,
    "comment": "Sell stop order"
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()

confirmation = stream_socket.recv_string()
result = json.loads(confirmation)
```

**Use Case:** Enter sell position on breakdown below support.

---

## Position Management

### 7. Modify Position (Change SL/TP)

Modify the stop loss and/or take profit of an existing position.

**Request:**
```python
command = {
    "action": "TRADE",
    "actionType": "POSITION_MODIFY",
    "id": 123456789,          # Position ID (from POSITIONS command)
    "stoploss": 35100.00,     # New stop loss
    "takeprofit": 35600.00    # New take profit
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()

confirmation = stream_socket.recv_string()
result = json.loads(confirmation)
```

**Use Case:** Trail stop loss, adjust take profit based on market conditions.

### 8. Close Position Partially

Close part of a position while keeping the rest open.

**Request:**
```python
command = {
    "action": "TRADE",
    "actionType": "POSITION_PARTIAL",
    "id": 123456789,
    "volume": 0.05  # Close 0.05 lots out of 0.1 total
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()

confirmation = stream_socket.recv_string()
result = json.loads(confirmation)
```

**Use Case:** Take partial profits, reduce risk.

### 9. Close Position by ID

Close an entire position using its ID.

**Request:**
```python
command = {
    "action": "TRADE",
    "actionType": "POSITION_CLOSE_ID",
    "id": 123456789
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()

confirmation = stream_socket.recv_string()
result = json.loads(confirmation)
```

**Use Case:** Close specific position.

### 10. Close All Positions by Symbol

Close all positions for a specific symbol.

**Request:**
```python
command = {
    "action": "TRADE",
    "actionType": "POSITION_CLOSE_SYMBOL",
    "symbol": "BTCUSD"
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()

confirmation = stream_socket.recv_string()
result = json.loads(confirmation)
```

**Use Case:** Close all BTCUSD positions at once.

---

## Order Management

### 11. Modify Pending Order

Change the entry price, SL, or TP of a pending order.

**Request:**
```python
command = {
    "action": "TRADE",
    "actionType": "ORDER_MODIFY",
    "id": 987654321,          # Order ticket number
    "price": 35100.00,        # New entry price
    "stoploss": 35000.00,     # New stop loss
    "takeprofit": 35300.00,   # New take profit
    "expiration": 1699910000  # New expiration (optional)
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()

confirmation = stream_socket.recv_string()
result = json.loads(confirmation)
```

**Use Case:** Adjust pending order parameters as market moves.

### 12. Cancel Pending Order

Delete a pending order before it executes.

**Request:**
```python
command = {
    "action": "TRADE",
    "actionType": "ORDER_CANCEL",
    "id": 987654321  # Order ticket number
}

system_socket.send_string(json.dumps(command))
ack = system_socket.recv_string()

confirmation = stream_socket.recv_string()
result = json.loads(confirmation)
```

**Use Case:** Cancel order that's no longer needed.

---

## Trade Result Codes

The `result.retcode` field indicates trade execution status:

| Code | Name | Description |
|------|------|-------------|
| 10009 | `TRADE_RETCODE_DONE` | Request completed successfully |
| 10004 | `TRADE_RETCODE_REQUOTE` | Requote - price changed |
| 10006 | `TRADE_RETCODE_REJECT` | Request rejected |
| 10007 | `TRADE_RETCODE_CANCEL` | Request canceled |
| 10008 | `TRADE_RETCODE_PLACED` | Order placed (pending order) |
| 10013 | `TRADE_RETCODE_INVALID` | Invalid request |
| 10014 | `TRADE_RETCODE_INVALID_VOLUME` | Invalid volume |
| 10015 | `TRADE_RETCODE_INVALID_PRICE` | Invalid price |
| 10016 | `TRADE_RETCODE_INVALID_STOPS` | Invalid stop levels |
| 10018 | `TRADE_RETCODE_MARKET_CLOSED` | Market is closed |
| 10019 | `TRADE_RETCODE_NO_MONEY` | Insufficient funds |
| 10025 | `TRADE_RETCODE_LOCKED` | Trading locked for this symbol |

---

## Complete Trading Example

```python
#!/usr/bin/env python3
"""
Complete trading example with error handling
"""
import zmq
import json
import time

class MT5Trader:
    def __init__(self, host="localhost"):
        self.context = zmq.Context()

        self.system_socket = self.context.socket(zmq.REQ)
        self.system_socket.connect(f"tcp://{host}:2201")
        self.system_socket.setsockopt(zmq.RCVTIMEO, 5000)

        self.stream_socket = context.socket(zmq.PULL)
        self.stream_socket.connect(f"tcp://{host}:2204")
        self.stream_socket.setsockopt(zmq.RCVTIMEO, 10000)

    def send_trade(self, command):
        """Send trade command and wait for confirmation"""
        self.system_socket.send_string(json.dumps(command))
        ack = self.system_socket.recv_string()

        # Wait for trade confirmation
        try:
            confirmation = self.stream_socket.recv_string()
            result = json.loads(confirmation)
            return result
        except zmq.Again:
            return {"error": "Timeout waiting for trade confirmation"}

    def market_buy(self, symbol, volume, sl=None, tp=None, comment=""):
        """Place market buy order"""
        command = {
            "action": "TRADE",
            "actionType": "ORDER_TYPE_BUY",
            "symbol": symbol,
            "volume": volume,
            "deviation": 10,
            "comment": comment
        }
        if sl is not None:
            command["stoploss"] = sl
        if tp is not None:
            command["takeprofit"] = tp

        result = self.send_trade(command)
        return self.process_result(result)

    def market_sell(self, symbol, volume, sl=None, tp=None, comment=""):
        """Place market sell order"""
        command = {
            "action": "TRADE",
            "actionType": "ORDER_TYPE_SELL",
            "symbol": symbol,
            "volume": volume,
            "deviation": 10,
            "comment": comment
        }
        if sl is not None:
            command["stoploss"] = sl
        if tp is not None:
            command["takeprofit"] = tp

        result = self.send_trade(command)
        return self.process_result(result)

    def close_position(self, position_id):
        """Close position by ID"""
        command = {
            "action": "TRADE",
            "actionType": "POSITION_CLOSE_ID",
            "id": position_id
        }

        result = self.send_trade(command)
        return self.process_result(result)

    def modify_position(self, position_id, sl=None, tp=None):
        """Modify position SL/TP"""
        command = {
            "action": "TRADE",
            "actionType": "POSITION_MODIFY",
            "id": position_id
        }
        if sl is not None:
            command["stoploss"] = sl
        if tp is not None:
            command["takeprofit"] = tp

        result = self.send_trade(command)
        return self.process_result(result)

    def process_result(self, result):
        """Process trade result and return simplified info"""
        if "error" in result:
            return {"success": False, "error": result["error"]}

        res = result.get("result", {})
        retcode = res.get("retcode", 0)
        retcode_name = res.get("result", "UNKNOWN")

        if retcode == 10009:  # TRADE_RETCODE_DONE
            return {
                "success": True,
                "order_id": res.get("order", 0),
                "deal_id": res.get("deal", 0),
                "volume": res.get("volume", 0),
                "price": res.get("price", 0),
                "message": res.get("comment", "Success")
            }
        else:
            return {
                "success": False,
                "error": retcode_name,
                "retcode": retcode,
                "message": res.get("comment", "Trade failed")
            }

    def close(self):
        self.system_socket.close()
        self.stream_socket.close()
        self.context.term()

# Usage example
if __name__ == "__main__":
    trader = MT5Trader()

    try:
        # Open buy position
        print("Opening buy position...")
        result = trader.market_buy(
            symbol="BTCUSD",
            volume=0.1,
            sl=34900.00,
            tp=35500.00,
            comment="Automated buy"
        )

        if result["success"]:
            print(f"✓ Trade successful!")
            print(f"  Order ID: {result['order_id']}")
            print(f"  Price: {result['price']:.2f}")
            print(f"  Volume: {result['volume']}")
        else:
            print(f"✗ Trade failed: {result['error']}")
            print(f"  Message: {result.get('message', 'N/A')}")

    finally:
        trader.close()
```

---

## Risk Management Best Practices

### 1. Always Use Stop Loss

```python
# ✗ BAD: No stop loss
command = {"action": "TRADE", "actionType": "ORDER_TYPE_BUY", ...}

# ✓ GOOD: Always include stop loss
command = {
    "action": "TRADE",
    "actionType": "ORDER_TYPE_BUY",
    "stoploss": 34900.00,
    ...
}
```

### 2. Validate Volume Before Trading

```python
def validate_volume(symbol, volume, balance):
    """Check if volume is appropriate for account size"""
    max_risk_percent = 0.02  # 2% risk per trade
    max_volume = (balance * max_risk_percent) / 100  # Simplified

    if volume > max_volume:
        print(f"Warning: Volume {volume} exceeds risk limit!")
        return False
    return True
```

### 3. Check Account Status Before Trading

```python
# Get account info first
account_command = {"action": "BALANCE"}
system_socket.send_string(json.dumps(account_command))
ack = system_socket.recv_string()
balance_data = json.loads(data_socket.recv_string())

# Check free margin
if balance_data['margin_free'] < 1000:
    print("Insufficient free margin - trade aborted")
    exit()

# Now safe to place trade
```

### 4. Handle Trade Failures Gracefully

```python
max_retries = 3
for attempt in range(max_retries):
    result = trader.market_buy("BTCUSD", 0.1, sl=34900, tp=35500)

    if result["success"]:
        print("Trade successful!")
        break
    elif result.get("retcode") == 10004:  # REQUOTE
        print(f"Requote on attempt {attempt + 1}, retrying...")
        time.sleep(1)
    else:
        print(f"Trade failed: {result['error']}")
        break
```

---

## See Also

- [Account Guide](ACCOUNT_GUIDE.md) - Check positions and orders
- [Live Data Guide](LIVE_DATA_GUIDE.md) - Get current prices for trading decisions
- [Historical Data Guide](HIST_DATA_GUIDE.md) - Analyze past data before trading
