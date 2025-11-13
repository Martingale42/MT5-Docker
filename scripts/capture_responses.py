#!/usr/bin/env python3
"""
Response Capture Script for MT5-Docker JsonAPI
Captures actual JSON responses from all ports to document format for Nautilus integration
"""

import zmq
import json
import time
import datetime
from pathlib import Path


# Configuration
HOST = "localhost"
SYS_PORT = 2201    # REQ socket - send commands
DATA_PORT = 2202   # PULL socket - receive command responses
LIVE_PORT = 2203   # PULL socket - receive live price data
STREAM_PORT = 2204 # PULL socket - receive trade events

# Output directory for captured responses
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "response_samples"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class ResponseCapture:
    def __init__(self, host=HOST):
        self.host = host
        self.context = zmq.Context()

        # System socket (REQ/REP) - for sending commands
        self.system_socket = self.context.socket(zmq.REQ)
        self.system_socket.connect(f"tcp://{host}:{SYS_PORT}")
        self.system_socket.setsockopt(zmq.RCVTIMEO, 5000)
        print(f"✓ Connected to System socket (REQ): tcp://{host}:{SYS_PORT}")

        # Data socket (PULL) - for receiving command responses
        self.data_socket = self.context.socket(zmq.PULL)
        self.data_socket.connect(f"tcp://{host}:{DATA_PORT}")
        self.data_socket.setsockopt(zmq.RCVTIMEO, 10000)
        print(f"✓ Connected to Data socket (PULL): tcp://{host}:{DATA_PORT}")

        # Live socket (PULL) - for receiving live price updates
        self.live_socket = self.context.socket(zmq.PULL)
        self.live_socket.connect(f"tcp://{host}:{LIVE_PORT}")
        self.live_socket.setsockopt(zmq.RCVTIMEO, 5000)
        print(f"✓ Connected to Live socket (PULL): tcp://{host}:{LIVE_PORT}")

        # Stream socket (PULL) - for receiving trade events
        self.stream_socket = self.context.socket(zmq.PULL)
        self.stream_socket.connect(f"tcp://{host}:{STREAM_PORT}")
        self.stream_socket.setsockopt(zmq.RCVTIMEO, 5000)
        print(f"✓ Connected to Stream socket (PULL): tcp://{host}:{STREAM_PORT}")

        self.captured_responses = {}

    def send_command_and_capture(self, action_name, command):
        """
        Send command to sys_port, get ACK, then capture response from data_port
        """
        print(f"\n{'='*60}")
        print(f"Capturing: {action_name}")
        print(f"{'='*60}")
        print(f"Sending command: {json.dumps(command, indent=2)}")

        # Send to sys_port
        self.system_socket.send_string(json.dumps(command))

        # Get ACK from sys_port
        try:
            ack = self.system_socket.recv_string()
            print(f"✓ System ACK: {ack}")
        except zmq.Again:
            print("✗ No ACK from system socket (timeout)")
            return None

        # Get actual response from data_port
        time.sleep(0.5)  # Small delay for MT5 to process
        try:
            response = self.data_socket.recv_string()
            data = json.loads(response)
            print(f"✓ Data response received ({len(response)} bytes)")

            # Save to file
            filename = f"{action_name.lower().replace(' ', '_')}.json"
            filepath = OUTPUT_DIR / filename
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✓ Saved to: {filepath}")

            # Store in memory
            self.captured_responses[action_name] = data

            # Print summary
            if isinstance(data, dict):
                if "error" in data:
                    print(f"  Error: {data.get('error')}")
                    print(f"  Description: {data.get('description', 'N/A')}")
                else:
                    print(f"  Keys: {list(data.keys())}")
                    if "data" in data and isinstance(data["data"], list):
                        print(f"  Data items: {len(data['data'])}")

            return data

        except zmq.Again:
            print("✗ No response from data socket (timeout)")
            return None
        except json.JSONDecodeError as e:
            print(f"✗ JSON decode error: {e}")
            return None

    def capture_streaming_data(self, socket_name, socket, duration_secs, save_name):
        """
        Capture streaming data from live or stream socket
        """
        print(f"\n{'='*60}")
        print(f"Capturing streaming data: {socket_name} ({duration_secs}s)")
        print(f"{'='*60}")

        messages = []
        start_time = time.time()
        count = 0

        while time.time() - start_time < duration_secs:
            try:
                msg = socket.recv_string()
                data = json.loads(msg)
                messages.append(data)
                count += 1

                # Print first message details
                if count == 1:
                    print(f"First message: {json.dumps(data, indent=2)}")
                elif count % 10 == 0:
                    print(f"  Received {count} messages...")

            except zmq.Again:
                time.sleep(0.1)
                continue
            except json.JSONDecodeError as e:
                print(f"✗ JSON decode error: {e}")
                continue

        print(f"✓ Captured {len(messages)} messages in {duration_secs}s")

        if messages:
            # Save sample messages
            filename = f"{save_name}.json"
            filepath = OUTPUT_DIR / filename
            # Save first 100 messages to avoid huge files
            sample = messages[:100]
            with open(filepath, 'w') as f:
                json.dump(sample, f, indent=2)
            print(f"✓ Saved {len(sample)} samples to: {filepath}")

            self.captured_responses[socket_name] = sample

        return messages

    def close(self):
        """Close all sockets"""
        self.system_socket.close()
        self.data_socket.close()
        self.live_socket.close()
        self.stream_socket.close()
        self.context.term()
        print("\n✓ All sockets closed")


def main():
    print("="*60)
    print("MT5-Docker JsonAPI Response Capture")
    print("="*60)
    print(f"Host: {HOST}")
    print(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    capture = ResponseCapture(host=HOST)

    try:
        # ============================================================
        # CAPTURE 1: INSTRUMENTS
        # ============================================================
        capture.send_command_and_capture(
            "INSTRUMENTS",
            {"action": "INSTRUMENTS"}
        )

        # ============================================================
        # CAPTURE 2: ACCOUNT
        # ============================================================
        capture.send_command_and_capture(
            "ACCOUNT",
            {"action": "ACCOUNT"}
        )

        # ============================================================
        # CAPTURE 3: CONFIG M1 (Subscribe to M1 bars)
        # ============================================================
        capture.send_command_and_capture(
            "CONFIG_M1",
            {
                "action": "CONFIG",
                "actionType": "CONFIG",
                "symbol": "XAUUSD.sml",
                "chartTF": "M1"
            }
        )

        # ============================================================
        # CAPTURE 5: HISTORY (Bar data)
        # ============================================================
        from_date = int(time.time()) - (7 * 24 * 60 * 60)  # 7 days ago
        capture.send_command_and_capture(
            "HISTORY_BARS",
            {
                "action": "HISTORY",
                "actionType": "DATA",
                "symbol": "XAUUSD.sml",
                "chartTF": "M1",
                "fromDate": from_date,
                "toDate": int(time.time())
            }
        )

        # ============================================================
        # CAPTURE 6: HISTORY (Tick data)
        # ============================================================
        from_date = int(time.time()) - 3600  # 1 hour ago
        capture.send_command_and_capture(
            "HISTORY_TICKS",
            {
                "action": "HISTORY",
                "actionType": "DATA",
                "symbol": "BTCUSD",
                "chartTF": "TICK",
                "fromDate": from_date,
                "toDate": int(time.time())
            }
        )

        # ============================================================
        # CAPTURE 7: POSITIONS
        # ============================================================
        capture.send_command_and_capture(
            "POSITIONS",
            {"action": "POSITIONS"}
        )

        # ============================================================
        # CAPTURE 8: ORDERS
        # ============================================================
        capture.send_command_and_capture(
            "ORDERS",
            {"action": "ORDERS"}
        )

        # ============================================================
        # CAPTURE 9: BALANCE
        # ============================================================
        capture.send_command_and_capture(
            "BALANCE",
            {"action": "BALANCE"}
        )

        # ============================================================
        # CAPTURE 10: LIVE STREAM (M1 bars)
        # ============================================================
        print("\n" + "="*60)
        print("Note: M1 bars only update every ~60 seconds when a minute closes")
        print("Waiting 70 seconds to capture at least one M1 bar update...")
        print("(This ensures we catch a bar close)")
        print("="*60)
        capture.capture_streaming_data(
            "LIVE_STREAM_M1",
            capture.live_socket,
            duration_secs=70,
            save_name="live_stream_m1"
        )

        # ============================================================
        # CAPTURE 11: CONFIG TICK (Subscribe for tick data)
        # ============================================================
        capture.send_command_and_capture(
            "CONFIG_TICK",
            {
                "action": "CONFIG",
                "actionType": "CONFIG",
                "symbol": "BTCUSD",
                "chartTF": "TICK"
            }
        )

        # ============================================================
        # CAPTURE 12: LIVE STREAM (TICK data)
        # ============================================================
        print("\n" + "="*60)
        print("Capturing tick data (should have multiple updates per second)...")
        print("="*60)
        capture.capture_streaming_data(
            "LIVE_STREAM_TICK",
            capture.live_socket,
            duration_secs=15,
            save_name="live_stream_tick"
        )

        # ============================================================
        # SUMMARY
        # ============================================================
        print("\n" + "="*60)
        print("CAPTURE SUMMARY")
        print("="*60)
        for name, data in capture.captured_responses.items():
            status = "✓ SUCCESS" if data else "✗ FAILED"
            if isinstance(data, list):
                print(f"{status} - {name} ({len(data)} items)")
            else:
                print(f"{status} - {name}")

        print(f"\nAll responses saved to: {OUTPUT_DIR}")
        print("="*60)

        # ============================================================
        # OPTIONAL: Capture trade execution if user confirms
        # ============================================================
        print("\n" + "="*60)
        print("OPTIONAL: Capture Trade Execution Responses")
        print("="*60)
        print("WARNING: This will submit REAL orders to MT5!")
        print("Only proceed if you're on a DEMO account and understand the risks.")
        response = input("Capture trade execution? (yes/no): ")

        if response.lower() == 'yes':
            # NOTE: Adjust symbol and volume based on your account
            # This is a small test trade
            print("\nSubmitting test BUY order...")
            capture.send_command_and_capture(
                "TRADE_BUY",
                {
                    "action": "TRADE",
                    "actionType": "ORDER_TYPE_BUY",
                    "symbol": "BTCUSD",
                    "volume": 0.01,  # Small volume for testing
                    "stoploss": 0,
                    "takeprofit": 0,
                    "deviation": 10,
                    "comment": "Test order from capture script"
                }
            )

            # Wait for trade confirmation on stream socket
            print("\nWaiting for trade confirmation on stream socket...")
            time.sleep(1)
            capture.capture_streaming_data(
                "TRADE_CONFIRMATION",
                capture.stream_socket,
                duration_secs=5,
                save_name="trade_confirmation"
            )
        else:
            print("Skipping trade execution capture")

    except KeyboardInterrupt:
        print("\n\n✗ Capture interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        capture.close()


if __name__ == "__main__":
    main()
