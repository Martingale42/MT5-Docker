#!/usr/bin/env python3
"""
Simple test script for JsonAPI ZeroMQ connectivity
Tests all 4 sockets: System (2201), Data (2202), Live (2203), Stream (2204)
"""

import zmq
import json
import time
import datetime

# Configuration
HOST = "localhost"  # Change to your server IP if remote
SYSTEM_PORT = 2201  # REQ socket - send commands
DATA_PORT = 2202    # PULL socket - receive command responses
LIVE_PORT = 2203    # PULL socket - receive live price data
STREAM_PORT = 2204  # PULL socket - receive trade events

class JsonAPIClient:
    def __init__(self, host=HOST):
        self.host = host
        self.context = zmq.Context()

        # System socket (REQ/REP) - for sending commands
        self.system_socket = self.context.socket(zmq.REQ)
        self.system_socket.connect(f"tcp://{host}:{SYSTEM_PORT}")
        print(f"✓ Connected to System socket (REQ): tcp://{host}:{SYSTEM_PORT}")

        # Data socket (PULL) - for receiving command responses
        self.data_socket = self.context.socket(zmq.PULL)
        self.data_socket.connect(f"tcp://{host}:{DATA_PORT}")
        print(f"✓ Connected to Data socket (PULL): tcp://{host}:{DATA_PORT}")

        # Live socket (PULL) - for receiving live price updates
        self.live_socket = self.context.socket(zmq.PULL)
        self.live_socket.connect(f"tcp://{host}:{LIVE_PORT}")
        print(f"✓ Connected to Live socket (PULL): tcp://{host}:{LIVE_PORT}")

        # Stream socket (PULL) - for receiving trade events
        self.stream_socket = self.context.socket(zmq.PULL)
        self.stream_socket.connect(f"tcp://{host}:{STREAM_PORT}")
        print(f"✓ Connected to Stream socket (PULL): tcp://{host}:{STREAM_PORT}")

        # Set socket timeouts
        self.system_socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
        self.data_socket.setsockopt(zmq.RCVTIMEO, 5000)
        self.live_socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second for live data
        self.stream_socket.setsockopt(zmq.RCVTIMEO, 1000)

    def send_command(self, action, **kwargs):
        """Send command via System socket"""
        command = {"action": action, **kwargs}
        message = json.dumps(command)
        print(f"\n→ Sending: {message}")
        self.system_socket.send_string(message)

        # Wait for ACK on System socket
        try:
            response = self.system_socket.recv_string()
            print(f"← System ACK: {response}")
            return response
        except zmq.Again:
            print("✗ No response from System socket (timeout)")
            return None

    def receive_data(self, print_full=True):
        """Receive data from Data socket"""
        try:
            message = self.data_socket.recv_string()
            data = json.loads(message)

            # For very large responses, just print summary
            if print_full and len(message) < 10000:
                print(f"← Data socket: {json.dumps(data, indent=2)}")
            elif not data.get("error", False):
                print(f"← Data socket: Received {len(message)} bytes of data")
                if "data" in data and isinstance(data["data"], list):
                    print(f"  Contains {len(data['data'])} items")
            else:
                print(f"← Data socket: {json.dumps(data, indent=2)}")

            return data
        except zmq.Again:
            return None
        except json.JSONDecodeError as e:
            print(f"✗ JSON decode error: {e}")
            print(f"  Message length: {len(message)} bytes")
            print(f"  First 500 chars: {message[:500]}")
            print(f"  Last 500 chars: {message[-500:]}")
            return {"error": True, "description": "JSON decode error", "raw_error": str(e)}

    def receive_live(self):
        """Receive live price data from Live socket"""
        try:
            message = self.live_socket.recv_string()
            data = json.loads(message)
            return data
        except zmq.Again:
            return None

    def receive_stream(self):
        """Receive trade events from Stream socket"""
        try:
            message = self.stream_socket.recv_string()
            data = json.loads(message)
            return data
        except zmq.Again:
            return None

    def close(self):
        """Close all sockets"""
        self.system_socket.close()
        self.data_socket.close()
        self.live_socket.close()
        self.stream_socket.close()
        self.context.term()
        print("\n✓ All sockets closed")


def test_basic_connectivity(client):
    """Test 1: Basic connectivity and account info"""
    print("\n" + "="*60)
    print("TEST 1: Get Account Information")
    print("="*60)

    client.send_command("ACCOUNT")
    time.sleep(0.5)
    data = client.receive_data()

    if data and not data.get("error", False):
        print("✓ Successfully retrieved account information")
        print(data)
        return True
    else:
        print("✗ Failed to retrieve account information")
        if data:
            print(f"  Error: {data.get('description', 'Unknown error')}")
        return False


def test_config_symbol(client):
    """Test 2: Configure/subscribe to a symbol"""
    print("\n" + "="*60)
    print("TEST 2: Configure Symbol (XAUUSD.sml, M1)")
    print("="*60)

    client.send_command("CONFIG", actionType="CONFIG", symbol="XAUUSD.sml", chartTF="M1")
    time.sleep(0.5)
    data = client.receive_data()

    if data and not data.get("error", False):
        print("✓ Successfully configured symbol")
        print(data)
        return True
    else:
        print("✗ Failed to configure symbol")
        if data:
            print(f"  Error: {data.get('description', 'Unknown error')}")
        return False


def test_market_data(client):
    """Test 3: Get market data (OHLC)"""
    print("\n" + "="*60)
    print("TEST 3: Get Market Data (XAUUSD.sml M1, last 100 bars)")
    print("="*60)

    # Get data from 7 days ago to now
    from_date = int(time.time()) - (7 * 24 * 60 * 60)

    client.send_command(
        "HISTORY",
        actionType="DATA",
        symbol="XAUUSD.sml",
        chartTF="M1",
        fromDate=from_date,
        toDate=int(time.time())
    )
    time.sleep(1)
    data = client.receive_data()

    if data and not data.get("error", False):
        print("✓ Successfully retrieved market data")
        # Don't print all data, just summary
        if "data" in data:
            print(f"  Received {len(data['data'])} bars")
        return True
    else:
        print("✗ Failed to retrieve market data")
        if data:
            print(f"  Error: {data.get('description', 'Unknown error')}")
        return False


def test_live_stream(client):
    """Test 4: Subscribe to live price stream"""
    print("\n" + "="*60)
    print("TEST 4: Live Price Stream (XAUUSD.sml, 70 seconds)")
    print("="*60)

    # First configure the symbol to enable live streaming
    # M1 bars update every 60 seconds, so we need to wait at least 60+ seconds
    print("Configuring XAUUSD.sml M1 for live streaming...")
    client.send_command("CONFIG", actionType="CONFIG", symbol="XAUUSD.sml", chartTF="M1")
    time.sleep(1)
    # Drain any response from data socket
    client.receive_data()

    print("\nListening for live prices (M1 bars update every ~60 seconds)...")
    print("Waiting for at least one M1 bar to complete...")
    count = 0
    start_time = time.time()

    while time.time() - start_time < 70:  # Listen for 70 seconds to catch at least one M1 bar
        data = client.receive_live()
        if data:
            count += 1
            symbol = data.get('symbol', 'N/A')
            timeframe = data.get('timeframe', 'N/A')
            status = data.get('status', 'N/A')

            # Parse bar data from nested 'data' array
            bar_data = data.get('data', [])
            if isinstance(bar_data, list) and len(bar_data) >= 6:
                bar_time = time.strftime('%H:%M:%S', time.localtime(bar_data[0]))
                o, h, l, c, v = bar_data[1], bar_data[2], bar_data[3], bar_data[4], bar_data[5]
                print(f"  [{count}] {symbol} {timeframe} @ {bar_time}: O={o}, H={h}, L={l}, C={c}, V={v} (Status: {status})")
            else:
                print(f"  [{count}] {symbol} {timeframe}: Status={status} (No bar data)")

    if count > 0:
        print(f"\n✓ Received {count} live price update(s)")
        return True
    else:
        print("\n✗ No live price updates received")
        print("  Note: M1 bars only update when a new minute starts")
        return False


def test_tick_stream(client):
    """Test 5: Subscribe to real-time tick stream (bid/ask prices)"""
    print("\n" + "="*60)
    print("TEST 5: Real-time Tick Stream (BTCUSD, 15 seconds)")
    print("="*60)

    # Configure symbol for tick data (real-time bid/ask updates)
    print("Configuring BTCUSD TICK for real-time bid/ask streaming...")
    client.send_command("CONFIG", actionType="CONFIG", symbol="BTCUSD", chartTF="TICK")
    time.sleep(1)
    # Drain any response from data socket
    client.receive_data()

    print("\nListening for tick data (updates on every price change)...")
    count = 0
    start_time = time.time()
    last_bid = None

    while time.time() - start_time < 15:  # Listen for 15 seconds
        data = client.receive_live()
        if data:
            count += 1
            symbol = data.get('symbol', 'N/A')

            # Parse tick data
            tick_data = data.get('data', [])
            if isinstance(tick_data, list) and len(tick_data) >= 3:
                tick_time_ms = tick_data[0]
                bid = tick_data[1]
                ask = tick_data[2]
                spread = ask - bid

                # Show change indicator
                change = ""
                if last_bid is not None:
                    if bid > last_bid:
                        change = "↑"
                    elif bid < last_bid:
                        change = "↓"

                print(f"Recieve @ [{datetime.datetime.fromtimestamp(tick_time_ms / 1000, tz=datetime.UTC)}]")
                print(f"  [{count}] {symbol}: Bid={bid:.2f} {change}, Ask={ask:.2f}, Spread={spread:.2f}")
                last_bid = bid

    if count > 0:
        print(f"\n✓ Received {count} tick update(s) in 15 seconds")
        print(f"  Average: {count/15:.1f} ticks/second")
        return True
    else:
        print("\n✗ No tick updates received")
        print("  Note: Tick data requires live market activity")
        return False


def test_economic_calendar(client):
    """Test 6: Get economic calendar data"""
    print("\n" + "="*60)
    print("TEST 6: Economic Calendar Data")
    print("="*60)

    # Get calendar data for the last 3 days (shorter period to reduce response size)
    from_date = int(time.time()) - (3 * 24 * 60 * 60)  # 3 days ago

    client.send_command(
        "CALENDAR",
        actionType="DATA",
        symbol="XAUUSD.sml",
        fromDate=from_date
    )
    time.sleep(1)
    data = client.receive_data(print_full=False)  # Don't print full calendar data

    if data and not data.get("error", False):
        print("✓ Successfully retrieved calendar data")
        if "data" in data and isinstance(data["data"], list):
            print(f"  Received {len(data['data'])} calendar events")
            if len(data["data"]) > 0:
                print(f"  Sample event: {data['data'][0]}")
        return True
    else:
        print("✗ Failed to retrieve calendar data")
        if data:
            error_desc = data.get('description', 'Unknown error')
            if 'raw_error' in data:
                print(f"  JSON Error: {data.get('raw_error', '')}")
            else:
                print(f"  Error: {error_desc}")
        return False


def main():
    print("="*60)
    print("JsonAPI ZeroMQ Connectivity Test")
    print("="*60)
    print(f"Host: {HOST}")
    print(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    try:
        # Create client and connect
        client = JsonAPIClient(host=HOST)

        # Run tests
        results = []
        results.append(("Account Info", test_basic_connectivity(client)))
        results.append(("Config Symbol", test_config_symbol(client)))
        results.append(("Market Data", test_market_data(client)))
        results.append(("Live Stream (M1 Bars)", test_live_stream(client)))
        results.append(("Tick Stream (Bid/Ask)", test_tick_stream(client)))
        results.append(("Economic Calendar", test_economic_calendar(client)))

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        for test_name, passed in results:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status} - {test_name}")

        passed = sum(1 for _, p in results if p)
        total = len(results)
        print(f"\nTotal: {passed}/{total} tests passed")
        print("="*60)

        # Close connections
        client.close()

        return 0 if passed == total else 1

    except KeyboardInterrupt:
        print("\n\n✗ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
