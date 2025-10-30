# MT5-Docker with JsonAPI ZeroMQ

MetaTrader 5 running in Docker with JsonAPI Expert Advisor for ZeroMQ-based communication.

## Features

- **MT5 64-bit** running on Wine in Alpine Linux (~250 MB)
- **JsonAPI.mq5** Expert Advisor with 4-socket ZeroMQ architecture
- **VNC access** for remote GUI management
- **Economic Calendar** support via ZeroMQ
- **Multi-socket architecture** for high-performance trading
- **Docker Compose** for easy deployment

## Architecture

JsonAPI uses 4 separate ZeroMQ sockets for different purposes:

- **Port 2201** - System socket (REQ/REP) - Commands
- **Port 2202** - Data socket (PUSH) - Query responses
- **Port 2203** - Live socket (PUSH) - Real-time price streaming
- **Port 2204** - Stream socket (PUSH) - Trade events

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Using Makefile

```bash
# Build and run
make run

# Access shell
make shell

# Stop container
make stop

# Clean up (remove container and volume)
make clean
```

## VNC Access

Connect to MT5 terminal via VNC:

- **URL**: `localhost:5900`
- **Username**: `root`
- **Password**: `root`

Once connected:
1. Wait for MT5 to fully load (~1-2 minutes)
2. Open Navigator → Expert Advisors
3. Drag `JsonAPI` onto any chart
4. Verify the EA is running (check Expert tab for "Bound 'System' socket..." messages)

## ZeroMQ Port Configuration

| Port | Socket Type | Purpose | Pattern |
|------|-------------|---------|---------|
| 2201 | System | Send commands | REQ/REP |
| 2202 | Data | Receive responses | PUSH/PULL |
| 2203 | Live | Receive live prices | PUSH/PULL |
| 2204 | Stream | Receive trade events | PUSH/PULL |

## Supported Actions

JsonAPI supports the following actions via ZeroMQ:

- `CONFIG` - Subscribe to symbol/timeframe streaming
- `ACCOUNT` - Get account information
- `BALANCE` - Get balance information
- `HISTORY` - Get historical OHLC data
- `TRADE` - Execute trades (market/limit/stop orders)
- `POSITIONS` - Get open positions
- `ORDERS` - Get pending orders
- `MARKETDEPTH` - Get market depth (Level 2)
- `CALENDAR` - Get economic calendar events
- `WATCHLIST` - Get subscribed symbols
- `RESET` - Clear subscriptions

## Python Client Example

### Basic Usage

```python
import zmq
import json

# Connect to sockets
context = zmq.Context()

# System socket (for commands)
sys_socket = context.socket(zmq.REQ)
sys_socket.connect("tcp://localhost:2201")

# Data socket (for responses)
data_socket = context.socket(zmq.PULL)
data_socket.connect("tcp://localhost:2202")

# Send command
command = {"action": "ACCOUNT"}
sys_socket.send_json(command)
ack = sys_socket.recv_json()  # "OK"

# Get response
account_info = data_socket.recv_json()
print(account_info)
```

### Live Streaming

```python
# Live socket (for price streaming)
live_socket = context.socket(zmq.PULL)
live_socket.connect("tcp://localhost:2203")

# Subscribe to EURUSD tick data
sys_socket.send_json({
    "action": "CONFIG",
    "symbol": "EURUSD",
    "chartTF": "TICK"
})
sys_socket.recv_json()  # "OK"

# Stream prices
while True:
    price_data = live_socket.recv_json()
    print(price_data)
```

### Economic Calendar

```python
# Get calendar events for EURUSD
calendar_request = {
    "action": "CALENDAR",
    "actionType": "DATA",
    "symbol": "EURUSD",
    "fromDate": 1704067200,  # Unix timestamp: 2024-01-01
    "toDate": 1706745600     # Unix timestamp: 2024-02-01
}

sys_socket.send_json(calendar_request)
sys_socket.recv_json()  # "OK"

# Get calendar data from data socket
calendar = data_socket.recv_json()
print(calendar)
```

### Place Trade

```python
# Market buy order
trade_request = {
    "action": "TRADE",
    "actionType": "ORDER_TYPE_BUY",
    "symbol": "EURUSD",
    "volume": 0.01,
    "stoploss": 1.08,
    "takeprofit": 1.10,
    "price": 0,
    "deviation": 5,
    "comment": "Python bot"
}

sys_socket.send_json(trade_request)
sys_socket.recv_json()  # "OK"

# Get trade result from data socket
result = data_socket.recv_json()
print(f"Order: {result['order']}, Price: {result['price']}")
```

## Technical Details

### Base Image
- `ejtrader/pyzmq:dev` (Alpine 3.15 with Python3 and ZeroMQ)

### Components
- **MT5**: Latest version, auto-updates
- **Wine**: 64-bit, Windows 10 compatibility
- **ZeroMQ**: libzmq 4.2.0 + libsodium 1.0.11
- **VNC**: x11vnc with Openbox window manager
- **Process Manager**: Supervisord

### File Locations (Inside Container)
- MT5 Terminal: `/root/Metatrader/terminal64.exe`
- MQL5 Files: `/root/Metatrader/MQL5/`
- Expert Advisors: `/root/Metatrader/MQL5/Experts/`
- Logs: Check supervisord logs or MT5 Experts tab

## Troubleshooting

### EA Not Loading
1. Check DLL imports are enabled (Tools → Options → Expert Advisors)
2. Check "Allow algorithmic trading" is enabled
3. Verify ports 2201-2204 are not in use: `netstat -an | grep 220`

### Connection Timeout
1. Ensure EA is attached to a chart
2. Check MT5 Experts tab for "Bound 'System' socket..." messages
3. Try restarting the container: `docker-compose restart`

### Can't Connect to VNC
1. Check port 5900 is exposed: `docker ps`
2. Wait 1-2 minutes for X11 and MT5 to fully start
3. Check logs: `docker-compose logs`

## License

Based on MT5-ZeroMQ (GPL v3) and Metatrader5-Docker projects.

## Credits

- **JsonAPI**: Nikolai Khramkov
- **mql-zmq**: Ding Li
- **Base Docker**: ejtraderLabs
