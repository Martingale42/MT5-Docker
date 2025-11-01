#!/bin/sh
# Wait for X server to be ready
sleep 2
# Create VNC password file
mkdir -p /root/.vnc
x11vnc -storepasswd mt5pass /root/.vnc/passwd
# Start x11vnc with password
/usr/bin/x11vnc -xkb -noxrecord -noxfixes -noxdamage -display :0 -repeat -rfbauth /root/.vnc/passwd -wait 5 -permitfiletransfer -tightfilexfer -forever -shared


