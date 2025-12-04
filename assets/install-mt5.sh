#!/bin/sh
# MT5 Installation Script
# Downloads and extracts MT5 portable version

set -e

# Check if MT5 is already installed
if [ -f "/root/Metatrader/terminal64.exe" ]; then
    echo "MT5 is already installed at /root/Metatrader/terminal64.exe"
    exit 0
fi

echo "MT5 not found, downloading stable version..."

# Create temp directory
mkdir -p /tmp/mt5install
cd /tmp/mt5install

# Download MT5 setup using curl
echo "Downloading MT5 setup..."
curl -L -o mt5setup.exe "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe" || \
curl -L -o mt5setup.exe "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe?utm_source=www.metatrader5.com"

if [ ! -f "mt5setup.exe" ]; then
    echo "Failed to download MT5 setup"
    exit 1
fi

echo "Extracting MT5 files..."
# Try to extract the installer using 7z or cabextract
if command -v 7z >/dev/null 2>&1; then
    7z x -y mt5setup.exe
elif command -v cabextract >/dev/null 2>&1; then
    cabextract -q mt5setup.exe
else
    echo "No extraction tool available, trying Wine method..."
    # Wait for X server
    DISPLAY=:0
    export DISPLAY
    timeout=30
    while [ $timeout -gt 0 ]; do
        if xdpyinfo >/dev/null 2>&1; then
            break
        fi
        sleep 1
        timeout=$((timeout - 1))
    done

    # Run installer in silent mode
    wine mt5setup.exe /S /D=C:\\MT5 2>/dev/null &
    WINE_PID=$!
    sleep 45
    kill $WINE_PID 2>/dev/null || true
fi

# Search for MT5 files
echo "Searching for MT5 installation..."
MT5_PATH=$(find /root/.wine/drive_c -name "terminal64.exe" -type f 2>/dev/null | head -1)

if [ -n "$MT5_PATH" ] && [ -f "$MT5_PATH" ]; then
    echo "Found MT5 at: $MT5_PATH"
    MT5_DIR=$(dirname "$MT5_PATH")
    echo "Copying MT5 to /root/Metatrader..."
    mkdir -p /root/Metatrader
    cp -r "$MT5_DIR"/* /root/Metatrader/
    echo "MT5 installation completed successfully"
    echo "Cleaning up..."
    cd /
    rm -rf /tmp/mt5install
    exit 0
fi

# If still not found, try current directory extraction
MT5_PATH=$(find /tmp/mt5install -name "terminal64.exe" -type f 2>/dev/null | head -1)
if [ -n "$MT5_PATH" ] && [ -f "$MT5_PATH" ]; then
    echo "Found extracted MT5 at: $MT5_PATH"
    MT5_DIR=$(dirname "$MT5_PATH")
    echo "Copying MT5 to /root/Metatrader..."
    mkdir -p /root/Metatrader
    cp -r "$MT5_DIR"/* /root/Metatrader/
    echo "MT5 installation completed successfully"
    cd /
    rm -rf /tmp/mt5install
    exit 0
fi

echo "ERROR: MT5 installation failed - terminal64.exe not found"
echo "Please check logs and consider using pre-installed MT5"
cd /
rm -rf /tmp/mt5install
exit 1
