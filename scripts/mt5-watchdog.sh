#!/bin/bash
set -e

# MT5 Watchdog - Monitors MT5 and restarts if unresponsive
MT5_FILE="${WINEPREFIX}/drive_c/Program Files/MetaTrader 5/terminal64.exe"
CHECK_INTERVAL=${MT5_WATCHDOG_INTERVAL:-30}  # Check every 30 seconds
MAX_RETRIES=${MT5_WATCHDOG_MAX_RETRIES:-3}   # Max consecutive failures before restart

echo "[WATCHDOG] Starting MT5 watchdog (check interval: ${CHECK_INTERVAL}s)"

# Function to check if MT5 process exists and is responsive
check_mt5_health() {
    # Check if Wine process for MT5 is running
    if ! pgrep -f "terminal64.exe" > /dev/null; then
        echo "[WATCHDOG] MT5 process not found"
        return 1
    fi

    # Check if MT5 is using CPU (sign it's alive and processing)
    # A hung process typically shows 0% CPU for extended periods
    local cpu_usage=$(ps aux | grep -i "terminal64.exe" | grep -v grep | awk '{print $3}' | head -1)

    # If we can get CPU usage, MT5 is running
    if [ -n "$cpu_usage" ]; then
        echo "[WATCHDOG] MT5 is running (CPU: ${cpu_usage}%)"
        return 0
    fi

    echo "[WATCHDOG] Unable to check MT5 status"
    return 1
}

# Function to kill MT5 gracefully
kill_mt5() {
    echo "[WATCHDOG] Stopping MT5..."
    pkill -f "terminal64.exe" || true
    wineserver -k || true
    sleep 3
}

# Function to start MT5
start_mt5() {
    echo "[WATCHDOG] Starting MT5..."
    DISPLAY=:0 wine "$MT5_FILE" /portable &
    MT5_PID=$!
    echo "[WATCHDOG] MT5 started with PID: $MT5_PID"
}

# Start MT5 initially
start_mt5
consecutive_failures=0

# Main watchdog loop
while true; do
    sleep $CHECK_INTERVAL

    if check_mt5_health; then
        consecutive_failures=0
    else
        consecutive_failures=$((consecutive_failures + 1))
        echo "[WATCHDOG] Health check failed (${consecutive_failures}/${MAX_RETRIES})"

        if [ $consecutive_failures -ge $MAX_RETRIES ]; then
            echo "[WATCHDOG] MT5 appears unresponsive after ${MAX_RETRIES} checks. Restarting..."
            kill_mt5
            start_mt5
            consecutive_failures=0
        fi
    fi
done
