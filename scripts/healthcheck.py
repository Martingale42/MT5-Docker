#!/usr/bin/env python3
"""
Docker healthcheck script for MT5-Docker container

This script checks if the MT5 JsonAPI is responsive by:
1. Checking if ZMQ ports are listening
2. (Optional) Sending a ping command to verify MT5 is responding

Exit codes:
- 0: Healthy
- 1: Unhealthy
"""

import sys
import socket
import time

# Ports to check
PORTS = {
    2201: "System Socket (REQ/REP)",
    2202: "Data Socket (PUSH/PULL)",
    2203: "Live Socket (PUSH/PULL)",
    2204: "Stream Socket (PUSH/PULL)"
}

def check_port(host: str, port: int, timeout: float = 1.0) -> bool:
    """
    Check if a TCP port is listening.

    Args:
        host: Hostname to check
        port: Port number
        timeout: Connection timeout in seconds

    Returns:
        True if port is open, False otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def main():
    """Main healthcheck logic"""
    host = "localhost"
    failed_checks = []

    # Check all required ports
    for port, description in PORTS.items():
        if not check_port(host, port):
            failed_checks.append(f"Port {port} ({description}) is not accessible")

    # Report results
    if failed_checks:
        print("UNHEALTHY: The following checks failed:")
        for failure in failed_checks:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print("HEALTHY: All ZMQ ports are accessible")
        sys.exit(0)


if __name__ == "__main__":
    main()
