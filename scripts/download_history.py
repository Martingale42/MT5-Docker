#!/usr/bin/env python3
"""
Download historical data for XAUUSD.sml from 2020 to current time
"""

import json
import time
from datetime import datetime

import pandas as pd
import zmq

# Configuration
HOST = "localhost"
SYSTEM_PORT = 2201
DATA_PORT = 2202

SYMBOL = "XAUUSD.sml"
TIMEFRAME = "H1"  # Start with H1 (hourly), can change to M1 if needed
FROM_DATE = int(datetime(2020, 1, 1).timestamp())  # Jan 1, 2020
TO_DATE = int(time.time())  # Current time


class HistoryDownloader:
    def __init__(self, host=HOST):
        self.context = zmq.Context()

        # System socket (REQ/REP)
        self.system_socket = self.context.socket(zmq.REQ)
        self.system_socket.connect(f"tcp://{host}:{SYSTEM_PORT}")
        self.system_socket.setsockopt(zmq.RCVTIMEO, 10000)  # 10 second timeout

        # Data socket (PULL)
        self.data_socket = self.context.socket(zmq.PULL)
        self.data_socket.connect(f"tcp://{host}:{DATA_PORT}")
        self.data_socket.setsockopt(
            zmq.RCVTIMEO, 300000
        )  # 300 second (5 minute) timeout for very large data

        print("✓ Connected to JsonAPI")
        print(f"  System socket: tcp://{host}:{SYSTEM_PORT}")
        print(f"  Data socket: tcp://{host}:{DATA_PORT}")

    def download_history(self, symbol, timeframe, from_date, to_date):
        """Download historical data"""
        print(f"\n{'=' * 60}")
        print("Downloading Historical Data")
        print(f"{'=' * 60}")
        print(f"Symbol: {symbol}")
        print(f"Timeframe: {timeframe}")
        print(
            f"From: {datetime.fromtimestamp(from_date).strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print(f"To: {datetime.fromtimestamp(to_date).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Period: {(to_date - from_date) / 86400:.1f} days")
        print()

        # Send request
        command = {
            "action": "HISTORY",
            "actionType": "DATA",
            "symbol": symbol,
            "chartTF": timeframe,
            "fromDate": from_date,
            "toDate": to_date,
        }

        print("→ Sending request...")
        self.system_socket.send_string(json.dumps(command))

        # Wait for ACK
        ack = self.system_socket.recv_string()
        print(f"← System ACK: {ack}")

        if ack != "OK":
            print("✗ System did not acknowledge request")
            return None

        # Receive data
        print("← Waiting for historical data (this may take a while)...")
        if timeframe == "M1":
            print("   Note: M1 data from 2020 is very large, this may take 1-5 minutes...")
        start_time = time.time()

        try:
            message = self.data_socket.recv_string()
            elapsed = time.time() - start_time
            print(f"← Received response in {elapsed:.2f} seconds ({elapsed/60:.1f} minutes)")
            print(f"   Message size: {len(message):,} bytes ({len(message)/1024/1024:.1f} MB)")

            # Parse JSON
            print("← Parsing JSON...")
            data = json.loads(message)

            # Check for errors
            if data.get("error", False):
                print("✗ Error from MT5:")
                print(f"  Code: {data.get('lastError')}")
                print(f"  Description: {data.get('description')}")
                print(f"  Function: {data.get('function')}")
                return None

            # Extract bars
            if "data" not in data:
                print("✗ No 'data' field in response")
                print(f"  Response: {json.dumps(data)}")
                print("\n  Possible causes:")
                print("  - Symbol not available on this broker")
                print("  - Date range has no data (markets closed)")
                print("  - Symbol name incorrect (check MT5 Market Watch)")
                return None

            if not isinstance(data["data"], list):
                print("✗ 'data' field is not a list")
                return None

            if len(data["data"]) == 0:
                print("✗ No bars returned (empty data array)")
                print("  This usually means:")
                print("  - The date range has no trading data")
                print("  - Markets were closed during this period")
                print("  - Try a different date range or symbol")
                return None

            bars = data["data"]
            print(f"✓ Successfully received {len(bars):,} bars")

            return {
                "symbol": data.get("symbol", symbol),
                "timeframe": data.get("timeframe", timeframe),
                "bars": bars,
            }

        except zmq.Again:
            print("✗ Timeout waiting for data (waited 5 minutes)")
            print("\n  Possible solutions:")
            print("  1. Try a smaller date range (e.g., 1 year instead of 5 years)")
            print("  2. Use H1 or H4 timeframe instead of M1")
            print("  3. Download in chunks (multiple smaller requests)")
            return None
        except json.JSONDecodeError as e:
            print(f"✗ JSON decode error: {e}")
            return None
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            import traceback

            traceback.print_exc()
            return None

    def save_to_csv(self, data, filename):
        """Save bars to CSV file"""
        if not data or "bars" not in data:
            print("✗ No data to save")
            return False

        bars = data["bars"]
        symbol = data["symbol"]
        timeframe = data["timeframe"]

        print(f"\n{'=' * 60}")
        print("Saving to CSV")
        print(f"{'=' * 60}")

        # Convert to DataFrame
        df = pd.DataFrame(
            bars, columns=["time", "open", "high", "low", "close", "volume"]
        )

        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["time"], unit="s")

        # Reorder columns
        df = df[["timestamp", "time", "open", "high", "low", "close", "volume"]]

        # Save to CSV
        df.to_csv(filename, index=False)

        print(f"✓ Saved to {filename}")
        print(f"  Rows: {len(df):,}")
        print(f"  Columns: {', '.join(df.columns)}")
        print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"  File size: {len(open(filename, 'rb').read()):,} bytes")

        # Show sample data
        print("\nFirst 5 bars:")
        print(df.head().to_string())
        print("\nLast 5 bars:")
        print(df.tail().to_string())

        return True

    def close(self):
        """Close sockets"""
        self.system_socket.close()
        self.data_socket.close()
        self.context.term()
        print("\n✓ Disconnected")


def main():
    import sys

    # Parse command line arguments
    timeframe = TIMEFRAME  # Default
    if "--timeframe" in sys.argv:
        idx = sys.argv.index("--timeframe")
        if idx + 1 < len(sys.argv):
            timeframe = sys.argv[idx + 1]
            print(f"Using timeframe: {timeframe}")

    print("=" * 60)
    print("MT5 Historical Data Downloader")
    print("=" * 60)
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    downloader = HistoryDownloader()

    try:
        # Download data with specified timeframe
        data = downloader.download_history(SYMBOL, timeframe, FROM_DATE, TO_DATE)

        if data:
            filename = f"{SYMBOL}_{timeframe}_2020-{datetime.now().year}.csv"
            downloader.save_to_csv(data, filename)

            # Show info about other timeframes
            if timeframe == "H1":
                print(f"\n{'=' * 60}")
                print("H1 download complete!")
                print(f"{'=' * 60}")
                print("\nNote: M1 data from 2020 will be MUCH larger (60x more bars)")
                print(f"Expected M1 bars: ~{len(data['bars']) * 60:,} bars")
                print("\nTo download M1 data, run:")
                print("  uv run python download_history.py --timeframe M1")
            elif timeframe == "M1":
                print(f"\n{'=' * 60}")
                print("M1 download complete!")
                print(f"{'=' * 60}")
                print(f"Successfully downloaded {len(data['bars']):,} M1 bars")
                print(f"File: {filename}")

    except KeyboardInterrupt:
        print("\n\n✗ Download interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        downloader.close()


if __name__ == "__main__":
    main()
