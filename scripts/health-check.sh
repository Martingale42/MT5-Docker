#!/bin/bash
# Docker health check script for MT5 container

# Check if MT5 process is running
if ! pgrep -f "terminal64.exe" > /dev/null; then
    echo "MT5 process not running"
    exit 1
fi

# Check if X server is running
if ! pgrep -f "Xvfb.*:0" > /dev/null; then
    echo "X server not running"
    exit 1
fi

# Check if VNC server is running
if ! pgrep -f "x11vnc" > /dev/null; then
    echo "VNC server not running"
    exit 1
fi

echo "MT5 container healthy"
exit 0
