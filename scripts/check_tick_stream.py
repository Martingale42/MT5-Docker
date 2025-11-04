#!/usr/bin/env python3
"""
Test real-time TICK data stream (bid/ask prices)
Unlike M1 bars which update every 60 seconds, TICK data updates on every price change
"""
import datetime
import zmq
import json
import time

HOST = "localhost"
SYSTEM_PORT = 2201
DATA_PORT = 2202
LIVE_PORT = 2203

context = zmq.Context()

# System socket
system_socket = context.socket(zmq.REQ)
system_socket.connect(f"tcp://{HOST}:{SYSTEM_PORT}")
system_socket.setsockopt(zmq.RCVTIMEO, 5000)

# Data socket
data_socket = context.socket(zmq.PULL)
data_socket.connect(f"tcp://{HOST}:{DATA_PORT}")
data_socket.setsockopt(zmq.RCVTIMEO, 1000)

# Live socket
live_socket = context.socket(zmq.PULL)
live_socket.connect(f"tcp://{HOST}:{LIVE_PORT}")
live_socket.setsockopt(zmq.RCVTIMEO, 1000)

print("Configuring BTCUSD for TICK data (real-time bid/ask)...")
system_socket.send_string(json.dumps({
    "action": "CONFIG",
    "actionType": "CONFIG",
    "symbol": "BTCUSD",
    "chartTF": "TICK"  # ← This is the key: use TICK instead of M1
}))
print(f"System ACK: {system_socket.recv_string()}")

# Drain data socket
try:
    data_socket.recv_string()
except:
    pass

print("\nListening for real-time tick data (30 seconds)...")
print("This should update on EVERY price change, not just bar closes")
print(f"Started at: {time.strftime('%H:%M:%S')}")
print("=" * 70)

start = time.time()
count = 0
last_bid = None
last_ask = None

while time.time() - start < 30:
    try:
        msg = live_socket.recv_string()
        count += 1
        data = json.loads(msg)
        current_time = time.strftime('%H:%M:%S')

        symbol = data.get('symbol', 'N/A')
        timeframe = data.get('timeframe', 'N/A')
        status = data.get('status', 'N/A')

        if 'data' in data:
            tick_data = data['data']
            if isinstance(tick_data, list) and len(tick_data) >= 3:
                tick_time_ms = tick_data[0]
                bid = tick_data[1]
                ask = tick_data[2]
                spread = ask - bid

                # Show price change indicator
                bid_change = ""
                ask_change = ""
                if last_bid is not None:
                    if bid > last_bid:
                        bid_change = "↑"
                    elif bid < last_bid:
                        bid_change = "↓"
                    if ask > last_ask:
                        ask_change = "↑"
                    elif ask < last_ask:
                        ask_change = "↓"

                print(f"[{datetime.datetime.fromtimestamp(tick_time_ms / 1_000, tz=datetime.UTC)}] #{count:3d} | {symbol:8s} | "
                      f"Bid: {bid:10.2f} {bid_change:1s} | "
                      f"Ask: {ask:10.2f} {ask_change:1s} | "
                      f"Spread: {spread:.2f}")

                last_bid = bid
                last_ask = ask

    except zmq.Again:
        pass

print("=" * 70)
print(f"Total tick updates received: {count}")
print(f"Average ticks per second: {count/30:.1f}")
print(f"Finished at: {time.strftime('%H:%M:%S')}")

system_socket.close()
data_socket.close()
live_socket.close()
context.term()
