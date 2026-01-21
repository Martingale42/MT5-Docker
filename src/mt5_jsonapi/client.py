"""
MT5 JsonAPI ZeroMQ Client

A client for communicating with the MT5 JsonAPI Expert Advisor
via ZeroMQ sockets.
"""

import zmq
import json
from typing import Dict, Any, Optional


class JsonAPIClient:
    """
    Client for MT5 JsonAPI ZeroMQ communication.

    Manages 4 sockets:
    - System socket (REQ): Send commands
    - Data socket (PULL): Receive command responses
    - Live socket (PULL): Receive live price updates
    - Stream socket (PULL): Receive trade events
    """

    def __init__(
        self,
        host: str = "localhost",
        system_port: int = 2201,
        data_port: int = 2202,
        live_port: int = 2203,
        stream_port: int = 2204,
        verbose: bool = False
    ):
        """
        Initialize the JsonAPI client.

        Args:
            host: MT5 server hostname
            system_port: System socket port (REQ)
            data_port: Data socket port (PULL)
            live_port: Live socket port (PULL)
            stream_port: Stream socket port (PULL)
            verbose: Enable verbose logging
        """
        self.host = host
        self.verbose = verbose
        self.context = zmq.Context()

        # System socket (REQ/REP) - for sending commands
        self.system_socket = self.context.socket(zmq.REQ)
        self.system_socket.connect(f"tcp://{host}:{system_port}")
        if verbose:
            print(f"✓ Connected to System socket (REQ): tcp://{host}:{system_port}")

        # Data socket (PULL) - for receiving command responses
        self.data_socket = self.context.socket(zmq.PULL)
        self.data_socket.connect(f"tcp://{host}:{data_port}")
        if verbose:
            print(f"✓ Connected to Data socket (PULL): tcp://{host}:{data_port}")

        # Live socket (PULL) - for receiving live price updates
        self.live_socket = self.context.socket(zmq.PULL)
        self.live_socket.connect(f"tcp://{host}:{live_port}")
        if verbose:
            print(f"✓ Connected to Live socket (PULL): tcp://{host}:{live_port}")

        # Stream socket (PULL) - for receiving trade events
        self.stream_socket = self.context.socket(zmq.PULL)
        self.stream_socket.connect(f"tcp://{host}:{stream_port}")
        if verbose:
            print(f"✓ Connected to Stream socket (PULL): tcp://{host}:{stream_port}")

        # Set socket timeouts
        self.system_socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
        self.data_socket.setsockopt(zmq.RCVTIMEO, 5000)
        self.live_socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second for live data
        self.stream_socket.setsockopt(zmq.RCVTIMEO, 1000)

    def send_command(self, action: str, **kwargs) -> Optional[str]:
        """
        Send command via System socket.

        Args:
            action: The action to perform (e.g., ACCOUNT, CONFIG, TRADE)
            **kwargs: Additional parameters for the command

        Returns:
            System socket ACK response, or None if timeout
        """
        command = {"action": action, **kwargs}
        message = json.dumps(command)

        if self.verbose:
            print(f"\n→ Sending: {message}")

        self.system_socket.send_string(message)

        # Wait for ACK on System socket
        try:
            response = self.system_socket.recv_string()
            if self.verbose:
                print(f"← System ACK: {response}")
            return response
        except zmq.Again:
            if self.verbose:
                print("✗ No response from System socket (timeout)")
            return None

    def receive_data(self, timeout_ms: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Receive data from Data socket.

        Args:
            timeout_ms: Optional custom timeout in milliseconds

        Returns:
            Parsed JSON data, or None if timeout/error
        """
        # Temporarily set custom timeout if provided
        if timeout_ms is not None:
            old_timeout = self.data_socket.getsockopt(zmq.RCVTIMEO)
            self.data_socket.setsockopt(zmq.RCVTIMEO, timeout_ms)

        try:
            message = self.data_socket.recv_string()
            data = json.loads(message)

            if self.verbose:
                if len(message) < 10000:
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
            if self.verbose:
                print(f"✗ JSON decode error: {e}")
                print(f"  Message length: {len(message)} bytes")
                print(f"  First 500 chars: {message[:500]}")
                print(f"  Last 500 chars: {message[-500:]}")
            return {"error": True, "description": "JSON decode error", "raw_error": str(e)}
        finally:
            # Restore original timeout
            if timeout_ms is not None:
                self.data_socket.setsockopt(zmq.RCVTIMEO, old_timeout)

    def receive_live(self, timeout_ms: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Receive live price data from Live socket.

        Args:
            timeout_ms: Optional custom timeout in milliseconds

        Returns:
            Parsed JSON data, or None if timeout
        """
        if timeout_ms is not None:
            old_timeout = self.live_socket.getsockopt(zmq.RCVTIMEO)
            self.live_socket.setsockopt(zmq.RCVTIMEO, timeout_ms)

        try:
            message = self.live_socket.recv_string()
            data = json.loads(message)
            return data
        except zmq.Again:
            return None
        finally:
            if timeout_ms is not None:
                self.live_socket.setsockopt(zmq.RCVTIMEO, old_timeout)

    def receive_stream(self, timeout_ms: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Receive trade events from Stream socket.

        Args:
            timeout_ms: Optional custom timeout in milliseconds

        Returns:
            Parsed JSON data, or None if timeout
        """
        if timeout_ms is not None:
            old_timeout = self.stream_socket.getsockopt(zmq.RCVTIMEO)
            self.stream_socket.setsockopt(zmq.RCVTIMEO, timeout_ms)

        try:
            message = self.stream_socket.recv_string()
            data = json.loads(message)
            return data
        except zmq.Again:
            return None
        finally:
            if timeout_ms is not None:
                self.stream_socket.setsockopt(zmq.RCVTIMEO, old_timeout)

    def close(self):
        """Close all sockets and terminate context"""
        self.system_socket.close()
        self.data_socket.close()
        self.live_socket.close()
        self.stream_socket.close()
        self.context.term()
        if self.verbose:
            print("\n✓ All sockets closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
