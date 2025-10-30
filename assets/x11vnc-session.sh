#!/bin/sh
# Wait for X server to be ready
sleep 2
/usr/bin/x11vnc -xkb -noxrecord -noxfixes -noxdamage -display :0 -repeat -nopw -wait 5 -permitfiletransfer -tightfilexfer -forever -shared


