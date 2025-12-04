#!/usr/bin/env python3
"""
Prometheus Metrics Exporter for MT5-Docker

Exposes metrics about MT5 JsonAPI operations for Prometheus scraping.

Metrics exposed:
- zmq_requests_total: Counter of requests by action type
- zmq_request_duration_seconds: Histogram of request latencies
- zmq_errors_total: Counter of errors by action type
- mt5_connection_status: Gauge (1=connected, 0=disconnected)
- mt5_account_balance: Gauge of account balance
- mt5_account_equity: Gauge of account equity

Usage:
    python3 prometheus_exporter.py --port 9090 --mt5-host localhost
"""

import argparse
import time
import sys
import logging
from pathlib import Path
from threading import Thread

# Add scripts directory to path for zmq_client
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

try:
    from prometheus_client import start_http_server, Counter, Histogram, Gauge, Info
    from zmq_client import JsonAPIClient
    import zmq
except ImportError as e:
    print(f"ERROR: Required module not installed: {e}")
    print("Install with: pip install prometheus-client pyzmq")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Define Prometheus metrics
zmq_requests_total = Counter(
    'zmq_requests_total',
    'Total number of ZMQ requests',
    ['action']
)

zmq_errors_total = Counter(
    'zmq_errors_total',
    'Total number of ZMQ errors',
    ['action', 'error_type']
)

zmq_request_duration_seconds = Histogram(
    'zmq_request_duration_seconds',
    'ZMQ request duration in seconds',
    ['action'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

mt5_connection_status = Gauge(
    'mt5_connection_status',
    'MT5 connection status (1=connected, 0=disconnected)'
)

mt5_account_balance = Gauge(
    'mt5_account_balance',
    'MT5 account balance'
)

mt5_account_equity = Gauge(
    'mt5_account_equity',
    'MT5 account equity'
)

mt5_account_margin = Gauge(
    'mt5_account_margin',
    'MT5 account margin used'
)

mt5_account_margin_free = Gauge(
    'mt5_account_margin_free',
    'MT5 account free margin'
)

mt5_info = Info(
    'mt5',
    'MT5 server information'
)


class MT5MetricsCollector:
    """Collects metrics from MT5 via ZMQ"""

    def __init__(self, host: str, update_interval: int = 30):
        """
        Initialize metrics collector.

        Args:
            host: MT5 server hostname
            update_interval: Seconds between metric updates
        """
        self.host = host
        self.update_interval = update_interval
        self.client = None
        self.running = False

    def connect(self) -> bool:
        """
        Connect to MT5 via ZMQ.

        Returns:
            True if connected successfully
        """
        try:
            logger.info(f"Connecting to MT5 at {self.host}")
            self.client = JsonAPIClient(host=self.host, verbose=False)

            # Test connection with BALANCE query
            start_time = time.time()
            ack = self.client.send_command("BALANCE")
            duration = time.time() - start_time

            if ack:
                zmq_requests_total.labels(action="BALANCE").inc()
                zmq_request_duration_seconds.labels(action="BALANCE").observe(duration)
                mt5_connection_status.set(1)
                logger.info("Connected to MT5 successfully")
                return True
            else:
                mt5_connection_status.set(0)
                zmq_errors_total.labels(action="BALANCE", error_type="timeout").inc()
                logger.error("Failed to connect: No ACK received")
                return False

        except Exception as e:
            mt5_connection_status.set(0)
            zmq_errors_total.labels(action="BALANCE", error_type="connection_error").inc()
            logger.error(f"Failed to connect to MT5: {e}")
            return False

    def collect_account_metrics(self):
        """Collect account balance and equity metrics"""
        try:
            start_time = time.time()

            # Send ACCOUNT command
            ack = self.client.send_command("ACCOUNT")

            if not ack:
                logger.warning("No ACK received for ACCOUNT command")
                return

            # Receive response
            time.sleep(0.5)  # Small delay for response
            data = self.client.receive_data(timeout_ms=5000)

            duration = time.time() - start_time
            zmq_requests_total.labels(action="ACCOUNT").inc()
            zmq_request_duration_seconds.labels(action="ACCOUNT").observe(duration)

            if data and not data.get("error", True):
                # Update account metrics
                mt5_account_balance.set(data.get("balance", 0))
                mt5_account_equity.set(data.get("equity", 0))
                mt5_account_margin.set(data.get("margin", 0))
                mt5_account_margin_free.set(data.get("margin_free", 0))

                # Update info metric
                mt5_info.info({
                    'broker': data.get('broker', 'unknown'),
                    'server': data.get('server', 'unknown'),
                    'currency': data.get('currency', 'unknown')
                })

                logger.debug(f"Account metrics updated: balance={data.get('balance')}")
            else:
                error_desc = data.get("description", "unknown error") if data else "no response"
                zmq_errors_total.labels(action="ACCOUNT", error_type="api_error").inc()
                logger.warning(f"Error retrieving account data: {error_desc}")

        except zmq.Again:
            zmq_errors_total.labels(action="ACCOUNT", error_type="timeout").inc()
            logger.warning("Timeout collecting account metrics")
        except Exception as e:
            zmq_errors_total.labels(action="ACCOUNT", error_type="exception").inc()
            logger.error(f"Error collecting account metrics: {e}")

    def run(self):
        """Main collection loop"""
        self.running = True
        logger.info(f"Starting metrics collection (interval: {self.update_interval}s)")

        while self.running:
            try:
                # Check connection
                if not self.client:
                    if not self.connect():
                        logger.warning("Connection failed, retrying in 10 seconds")
                        time.sleep(10)
                        continue

                # Collect metrics
                self.collect_account_metrics()

                # Wait for next collection
                time.sleep(self.update_interval)

            except KeyboardInterrupt:
                logger.info("Shutting down metrics collector")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                time.sleep(5)

        # Cleanup
        if self.client:
            self.client.close()
            mt5_connection_status.set(0)

    def start(self):
        """Start collector in background thread"""
        thread = Thread(target=self.run, daemon=True)
        thread.start()
        return thread


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="MT5 Prometheus Metrics Exporter")
    parser.add_argument(
        "--port",
        type=int,
        default=9090,
        help="Port to expose metrics on (default: 9090)"
    )
    parser.add_argument(
        "--mt5-host",
        type=str,
        default="localhost",
        help="MT5 server hostname (default: localhost)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Metrics collection interval in seconds (default: 30)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Start Prometheus HTTP server
    logger.info(f"Starting Prometheus exporter on port {args.port}")
    start_http_server(args.port)

    # Start metrics collector
    collector = MT5MetricsCollector(
        host=args.mt5_host,
        update_interval=args.interval
    )

    try:
        collector.run()
    except KeyboardInterrupt:
        logger.info("Exporter stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
