#!/usr/bin/env python3
"""
Quick test to see if live stream data is being sent from MT5
"""
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

print("Configuring BTCUSD M1...")
system_socket.send_string(json.dumps({"action": "CONFIG", "actionType": "CONFIG", "symbol": "BTCUSD", "chartTF": "M1"}))
print(f"System ACK: {system_socket.recv_string()}")

# Drain data socket
try:
    data_socket.recv_string()
except:
    pass

print("\nWaiting 150 seconds for live data (should catch 2-3 bar closes)...")
print(f"Started at: {time.strftime('%H:%M:%S')}")
print("=" * 60)

start = time.time()
count = 0

while time.time() - start < 150:
    try:
        msg = live_socket.recv_string()
        count += 1
        data = json.loads(msg)
        current_time = time.strftime('%H:%M:%S')
        print(f"[{current_time}] Update #{count}:")
        print(f"  Symbol: {data.get('symbol')}")
        print(f"  Timeframe: {data.get('timeframe')}")
        print(f"  Status: {data.get('status')}")
        if 'data' in data:
            bar_data = data['data']
            if isinstance(bar_data, list) and len(bar_data) >= 6:
                print(f"  Bar time: {time.strftime('%H:%M:%S', time.localtime(bar_data[0]))}")
                print(f"  OHLCV: O={bar_data[1]}, H={bar_data[2]}, L={bar_data[3]}, C={bar_data[4]}, V={bar_data[5]}")
        print()
    except zmq.Again:
        pass

    # Show progress every 10 seconds
    elapsed = int(time.time() - start)
    if elapsed % 10 == 0 and elapsed > 0:
        remaining = 150 - elapsed
        print(f"  ... {elapsed}s elapsed, {remaining}s remaining, {count} updates received so far")

print("=" * 60)
print(f"Total updates received: {count}")
print(f"Finished at: {time.strftime('%H:%M:%S')}")

system_socket.close()
data_socket.close()
live_socket.close()
context.term()
