#!/bin/bash
set -e

# Configuration
MT5_FILE="${WINEPREFIX}/drive_c/Program Files/MetaTrader 5/terminal64.exe"
MT5_MQL5_DIR="${WINEPREFIX}/drive_c/Program Files/MetaTrader 5/MQL5"
LOCAL_MQL5_DIR="/mql5"

echo "================================"
echo "MT5 Docker Startup"
echo "================================"
echo "WINEPREFIX: ${WINEPREFIX}"
echo "DISPLAY: ${DISPLAY}"

# Ensure /config directory exists
mkdir -p /config

# Check if Wine prefix exists, if not initialize it
if [ ! -d "${WINEPREFIX}" ]; then
    echo "[1/4] Initializing Wine prefix..."
    mkdir -p "${WINEPREFIX}"
    WINEDLLOVERRIDES="mscoree,mshtml=" wine wineboot --init
    wineserver -w
    echo "[1/4] Wine prefix initialized."
else
    echo "[1/4] Wine prefix already exists."
fi

# Check if MetaTrader 5 is already installed
if [ -e "$MT5_FILE" ]; then
    echo "[2/4] MetaTrader 5 is already installed at: $MT5_FILE"
else
    echo "[2/4] MetaTrader 5 not found. Installing..."

    # Set Windows 10 mode in Wine
    echo "[2/4] Setting Wine to Windows 10 mode..."
    wine reg add "HKEY_CURRENT_USER\\Software\\Wine" /v Version /t REG_SZ /d "win10" /f

    # Download MT5 installer
    echo "[2/4] Downloading MT5 installer..."
    mkdir -p /tmp/mt5install
    cd /tmp/mt5install
    curl -L -o mt5setup.exe "${MT5_INSTALLER_URL}"

    # Verify download
    if [ ! -f "mt5setup.exe" ]; then
        echo "[2/4] ERROR: Failed to download MT5 installer"
        exit 1
    fi

    FILE_SIZE=$(stat -f%z mt5setup.exe 2>/dev/null || stat -c%s mt5setup.exe)
    echo "[2/4] Downloaded MT5 installer (${FILE_SIZE} bytes)"

    # Start Xvfb for installation
    echo "[2/4] Starting Xvfb for installation..."
    Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
    XVFB_PID=$!
    export DISPLAY=:99
    sleep 3

    # Run MT5 installer
    echo "[2/4] Running MT5 installer... (this will take a few minutes)"
    wine /tmp/mt5install/mt5setup.exe /auto > /tmp/mt5_install.log 2>&1 &
    WINE_PID=$!

    # Wait for installation with progress indicators
    for i in {1..60}; do
        sleep 3
        if [ -e "$MT5_FILE" ]; then
            echo "[2/4] MT5 installation detected!"
            break
        fi
        if [ $((i % 10)) -eq 0 ]; then
            echo "[2/4] Still installing... ($((i*3)) seconds elapsed)"
        fi
    done

    # Cleanup installer processes
    kill $WINE_PID 2>/dev/null || true
    wineserver -w
    kill $XVFB_PID 2>/dev/null || true

    # Verify installation
    if [ -e "$MT5_FILE" ]; then
        echo "[2/4] MetaTrader 5 installed successfully!"
        rm -rf /tmp/mt5install
    else
        echo "[2/4] ERROR: MT5 installation failed"
        echo "[2/4] Check /tmp/mt5_install.log for details"
        cat /tmp/mt5_install.log
        exit 1
    fi
fi

# Handle MQL5 directory mounting
if [ -d "$LOCAL_MQL5_DIR" ] && [ "$(ls -A $LOCAL_MQL5_DIR)" ]; then
    echo "[3/4] Local MQL5 directory detected, setting up symlink..."
    # Backup original MQL5 if it exists
    if [ -d "$MT5_MQL5_DIR" ] && [ ! -L "$MT5_MQL5_DIR" ]; then
        echo "[3/4] Backing up original MQL5 directory..."
        mv "$MT5_MQL5_DIR" "${MT5_MQL5_DIR}.original"
    fi
    # Remove symlink if it exists
    if [ -L "$MT5_MQL5_DIR" ]; then
        rm "$MT5_MQL5_DIR"
    fi
    # Create symlink to local MQL5
    ln -sf "$LOCAL_MQL5_DIR" "$MT5_MQL5_DIR"
    echo "[3/4] MQL5 directory linked to $LOCAL_MQL5_DIR"
else
    echo "[3/4] No local MQL5 directory mounted, using default."
fi

# Start X server and VNC
echo "[4/4] Starting X server and VNC..."
Xvfb :0 -screen 0 1024x768x24 &
XVFB_PID=$!

# Wait for Xvfb to be ready
sleep 3
if ! ps -p $XVFB_PID > /dev/null; then
    echo "[4/4] ERROR: Xvfb failed to start"
    exit 1
fi

# Verify display is available
export DISPLAY=:0
xdpyinfo -display :0 >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[4/4] WARNING: Display :0 not ready, waiting..."
    sleep 2
fi

x11vnc -display :0 -forever -shared -rfbport 5900 -passwd "${VNC_PASSWORD:-mt5pass}" &
echo "[4/4] VNC server started on port 5900 (password protected)"

# Start openbox window manager
DISPLAY=:0 openbox &
sleep 1

# Start MetaTrader 5
echo "[4/4] Starting MetaTrader 5..."
echo "================================"
echo "MT5 is starting. Connect via VNC to view the GUI."
echo "================================"

# Start with watchdog if enabled, otherwise start directly
if [ "${MT5_WATCHDOG_ENABLED:-true}" = "true" ]; then
    echo "[4/4] Starting MT5 with watchdog monitoring..."
    /scripts/mt5-watchdog.sh
else
    echo "[4/4] Starting MT5 without watchdog..."
    DISPLAY=:0 wine "$MT5_FILE" /portable
fi
