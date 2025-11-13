#!/usr/bin/env python3
"""
Test script for SYMBOL_INFO action in JsonAPI.mq5
"""

import json
import time

import zmq


def test_symbol_info():
    """Test the SYMBOL_INFO action with various request formats"""

    # Setup ZMQ sockets
    context = zmq.Context()

    # Command socket (sys_port 2201) - sends requests
    sys_socket = context.socket(zmq.REQ)
    sys_socket.connect("tcp://localhost:2201")

    # Data socket (data_port 2202) - receives responses
    data_socket = context.socket(zmq.PULL)
    data_socket.connect("tcp://localhost:2202")

    print("=" * 80)
    print("Testing SYMBOL_INFO Action")
    print("=" * 80)

    # Test 1: Single symbol
    print("\n[TEST 1] Requesting single symbol: EURAUD")
    print("-" * 80)
    request1 = {"action": "SYMBOL_INFO", "symbol": "EURAUD"}
    sys_socket.send_string(json.dumps(request1))
    ack1 = sys_socket.recv_string()
    print(f"ACK: {ack1}")

    # Wait for response on data_port
    data_socket.setsockopt(zmq.RCVTIMEO, 3000)  # 3 second timeout
    try:
        response1 = data_socket.recv_string()
        print(f"\nResponse length: {len(response1)} chars")
        data = json.loads(response1)
        print(f"Error: {data.get('error')}")
        print(f"Number of symbols: {len(data.get('symbols', []))}")
        if data.get("symbols"):
            symbol = data["symbols"][0]
            print("\nSymbol details:")
            print(f"  symbol: {symbol.get('symbol')}")
            print(f"  description: {symbol.get('description')}")
            print(f"  base_currency: {symbol.get('base_currency')}")
            print(f"  quote_currency: {symbol.get('quote_currency')}")
            print(f"  digits: {symbol.get('digits')}")
            print(f"  contract_size: {symbol.get('contract_size')}")
            print(f"  tick_value: {symbol.get('tick_value')}")
            print(f"  tick_size: {symbol.get('tick_size')}")
            print(f"  volume_min: {symbol.get('volume_min')}")
            print(f"  volume_max: {symbol.get('volume_max')}")
            print(f"  bid: {symbol.get('bid')}")
            print(f"  ask: {symbol.get('ask')}")
    except zmq.error.Again:
        print("ERROR: Timeout waiting for response")
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON decode failed: {e}")
        print(f"Raw response: {response1[:200]}")

    time.sleep(1)

    # Test 2: Multiple symbols
    print("\n[TEST 2] Requesting multiple symbols: EURAUD, EURUSD")
    print("-" * 80)
    request2 = {"action": "SYMBOL_INFO", "symbols": ["EURAUD", "EURUSD"]}
    sys_socket.send_string(json.dumps(request2))
    ack2 = sys_socket.recv_string()
    print(f"ACK: {ack2}")

    try:
        response2 = data_socket.recv_string()
        print(f"\nResponse length: {len(response2)} chars")
        data = json.loads(response2)
        print(f"Error: {data.get('error')}")
        print(f"Number of symbols: {len(data.get('symbols', []))}")
        for symbol in data.get("symbols", []):
            print(f"  - {symbol.get('symbol')}: {symbol.get('description')}")
    except zmq.error.Again:
        print("ERROR: Timeout waiting for response")
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON decode failed: {e}")

    time.sleep(1)

    # Test 3: All symbols (limit output)
    print("\n[TEST 3] Requesting all symbols")
    print("-" * 80)
    request3 = {"action": "SYMBOL_INFO"}
    sys_socket.send_string(json.dumps(request3))
    ack3 = sys_socket.recv_string()
    print(f"ACK: {ack3}")

    try:
        response3 = data_socket.recv_string()
        print(f"\nResponse length: {len(response3)} chars")
        data = json.loads(response3)
        print(f"Error: {data.get('error')}")
        symbols = data.get("symbols", [])
        print(f"Total symbols received: {len(symbols)}")
        print("\nFirst 5 symbols:")
        for symbol in symbols[:5]:
            print(f"  - {symbol.get('symbol')}: {symbol.get('description')}")

        # Save full response to file
        output_file = "/home/cy/Code/MT5/MT5-Docker/data/response_samples/symbol_info_response.json"
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\nFull response saved to: {output_file}")

    except zmq.error.Again:
        print("ERROR: Timeout waiting for response")
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON decode failed: {e}")

    print("\n" + "=" * 80)
    print("Tests completed!")
    print("=" * 80)

    # Cleanup
    sys_socket.close()
    data_socket.close()
    context.term()


if __name__ == "__main__":
    test_symbol_info()
