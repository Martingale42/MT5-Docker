#!/usr/bin/env python3
"""
Download historical data from MT5 via JsonAPI.

Usage:
    python download_history.py XAUUSD.sml
    python download_history.py XAUUSD.sml --timeframe M1
    python download_history.py XAUUSD.sml --start 2020-01-01 --end 2025-01-01
    python download_history.py XAUUSD.sml -t H4 -s 2023-01-01
"""

import argparse
import json
import time
from datetime import datetime

import pandas as pd
import zmq

# Configuration
HOST = "localhost"
SYSTEM_PORT = 2201
DATA_PORT = 2202

# Default timeframe
DEFAULT_TIMEFRAME = "H1"
# Earliest possible date for MT5 history (broker-dependent, but this is a reasonable start)
EARLIEST_DATE = datetime(2000, 1, 1)


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
            zmq.RCVTIMEO, 3000000
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


def parse_date(date_str: str | None, default: datetime) -> datetime:
    """Parse date string in YYYY-MM-DD format, or return default if None."""
    if date_str is None:
        return default
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: '{date_str}'. Use YYYY-MM-DD format."
        )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download historical data from MT5 via JsonAPI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Parameters:
  Argument        Description                                       Default
  --------------- ------------------------------------------------- --------------
  symbol          Symbol to download (required)                     -
  -t, --timeframe Timeframe (M1, M5, M15, M30, H1, H4, D1, W1, MN1) H1
  -s, --start     Start date (YYYY-MM-DD)                           earliest
  -e, --end       End date (YYYY-MM-DD)                             now
  -o, --output    Output CSV filename                               auto-generated
  --host          JsonAPI host                                      localhost

Examples:
  %(prog)s XAUUSD.sml                              Download H1 data from earliest to now
  %(prog)s XAUUSD.sml -t M1                        Download M1 data
  %(prog)s XAUUSD.sml -s 2020-01-01                From 2020-01-01 to now
  %(prog)s XAUUSD.sml -s 2020-01-01 -e 2025-01-01  Specific date range
  %(prog)s EURUSD -t H4 -s 2023-06-01              EURUSD H4 from mid-2023
        """,
    )
    parser.add_argument(
        "symbol",
        help="Symbol to download (e.g., XAUUSD.sml, EURUSD)",
    )
    parser.add_argument(
        "-t", "--timeframe",
        default=DEFAULT_TIMEFRAME,
        help=f"Timeframe (default: {DEFAULT_TIMEFRAME})",
    )
    parser.add_argument(
        "-s", "--start",
        default=None,
        help="Start date in YYYY-MM-DD format (default: earliest available)",
    )
    parser.add_argument(
        "-e", "--end",
        default=None,
        help="End date in YYYY-MM-DD format (default: now)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output CSV filename (default: auto-generated)",
    )
    parser.add_argument(
        "--host",
        default=HOST,
        help=f"JsonAPI host (default: {HOST})",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Parse dates
    start_date = parse_date(args.start, EARLIEST_DATE)
    end_date = parse_date(args.end, datetime.now())

    # Convert to timestamps
    from_timestamp = int(start_date.timestamp())
    to_timestamp = int(end_date.timestamp())

    # Generate output filename if not specified
    if args.output:
        output_file = args.output
    else:
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        output_file = f"{args.symbol}_{args.timeframe}_{start_str}-{end_str}.csv"

    print("=" * 60)
    print("MT5 Historical Data Downloader")
    print("=" * 60)
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Symbol: {args.symbol}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Start: {start_date.strftime('%Y-%m-%d')} ({args.start or 'earliest'})")
    print(f"End: {end_date.strftime('%Y-%m-%d')} ({args.end or 'now'})")
    print(f"Output: {output_file}")
    print()

    downloader = HistoryDownloader(host=args.host)

    try:
        # Download data
        data = downloader.download_history(
            args.symbol, args.timeframe, from_timestamp, to_timestamp
        )

        if data:
            downloader.save_to_csv(data, output_file)

            print(f"\n{'=' * 60}")
            print(f"{args.timeframe} download complete!")
            print(f"{'=' * 60}")
            print(f"Successfully downloaded {len(data['bars']):,} bars")
            print(f"File: {output_file}")

            # Show tip for smaller timeframes
            if args.timeframe == "H1":
                print("\nTip: For M1 data, expect ~60x more bars:")
                print(f"  python {__file__} {args.symbol} -t M1 -s {args.start or '2020-01-01'}")

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
