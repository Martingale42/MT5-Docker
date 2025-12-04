FROM alpine:3.20 AS st-builder

RUN apk add --no-cache make gcc git freetype-dev \
            fontconfig-dev musl-dev xproto libx11-dev \
            libxft-dev libxext-dev
RUN git clone https://github.com/DenisKramer/st.git /work
WORKDIR /work
RUN make

FROM alpine:3.20 AS xdummy-builder

RUN apk add --no-cache make gcc freetype-dev \
            fontconfig-dev musl-dev xproto libx11-dev \
            libxft-dev libxext-dev avahi-libs libcrypto3 libssl3 libvncserver libx11 libxdamage libxext libxfixes libxi libxinerama libxrandr libxtst musl samba-winbind 
RUN apk add --no-cache linux-headers
RUN apk add x11vnc 
RUN Xdummy -install

# ----------------------------------------------------------------------------
# Build pyzmq on Alpine 3.20
FROM alpine:3.20 AS pyzmq-builder

RUN apk add --no-cache python3 py3-pip python3-dev gcc g++ musl-dev \
    zeromq-dev libsodium-dev && \
    python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir pyzmq

# ----------------------------------------------------------------------------

FROM alpine:3.20

USER root
# Copy Python and pyzmq from builder
COPY --from=pyzmq-builder /opt/venv /opt/venv
RUN apk add --no-cache python3 libzmq && \
    ln -sf /opt/venv/bin/python3 /usr/local/bin/python3 && \
    ln -sf /opt/venv/bin/pip /usr/local/bin/pip
ENV WINEPREFIX=/root/.wine
ENV WINEARCH=win64
ENV DISPLAY=:0
ENV USER=root
ENV PASSWORD=root


# Basic init and admin tools
RUN apk --no-cache add supervisor sudo wget \
    && echo "$USER:$PASSWORD" | /usr/sbin/chpasswd \
    && rm -rf /apk /tmp/* /var/cache/apk/*

# Install X11 server and dummy device
RUN apk add --no-cache xorg-server xf86-video-dummy x11vnc xdpyinfo \
    && rm -rf /apk /tmp/* /var/cache/apk/*
COPY --from=xdummy-builder /usr/bin/Xdummy.so /usr/bin/Xdummy.so
COPY assets/xorg.conf /etc/X11/xorg.conf
COPY assets/xorg.conf.d /etc/X11/xorg.conf.d

# Configure init
COPY assets/supervisord.conf /etc/supervisord.conf

# Openbox window manager
RUN apk --no-cache add openbox  \
    && rm -rf /apk /tmp/* /var/cache/apk/*
COPY assets/openbox/mayday/mayday-arc /usr/share/themes/mayday-arc
COPY assets/openbox/mayday/mayday-arc-dark /usr/share/themes/mayday-arc-dark
COPY assets/openbox/mayday/mayday-grey /usr/share/themes/mayday-grey
COPY assets/openbox/mayday/mayday-plane /usr/share/themes/mayday-plane
COPY assets/openbox/mayday/thesis /usr/share/themes/thesis
COPY assets/openbox/rc.xml /etc/xdg/openbox/rc.xml
COPY assets/openbox/menu.xml /etc/xdg/openbox/menu.xml
# Login Manager
RUN apk --no-cache add slim consolekit \
    && rm -rf /apk /tmp/* /var/cache/apk/*
RUN /usr/bin/dbus-uuidgen --ensure=/etc/machine-id
COPY assets/slim/slim.conf /etc/slim.conf
COPY assets/slim/alpinelinux /usr/share/slim/themes/alpinelinux

# A decent system font
RUN apk add --no-cache font-noto \
    && rm -rf /apk /tmp/* /var/cache/apk/*
COPY assets/fonts.conf /etc/fonts/fonts.conf



# st  as terminal
RUN apk add --no-cache freetype fontconfig xproto libx11 libxft libxext ncurses \
    && rm -rf /apk /tmp/* /var/cache/apk/*
COPY --from=st-builder /work/st /usr/bin/st
COPY --from=st-builder /work/st.info /etc/st/st.info
RUN tic -sx /etc/st/st.info

# Some other resources
RUN apk add --no-cache xset \
    && rm -rf /apk /tmp/* /var/cache/apk/*
COPY assets/xinit/Xresources /etc/X11/Xresources
COPY assets/xinit/xinitrc.d /etc/X11/xinit/xinitrc.d

COPY assets/x11vnc-session.sh /root/x11vnc-session.sh
COPY assets/start.sh /root/start.sh

# Install Wine 10.x from edge repository and dependencies
RUN apk update && \
    apk add --no-cache samba-winbind unzip cabextract curl p7zip xvfb bash && \
    apk add --no-cache wine --repository=http://dl-cdn.alpinelinux.org/alpine/edge/community --allow-untrusted

# Initialize Wine prefix to avoid prompts on first run
ENV WINEDLLOVERRIDES="mscoree,mshtml="
RUN wineboot -u && wineserver -w

# Download and install MT5 during build using Xvfb
RUN mkdir -p /root/Metatrader /tmp/mt5install && \
    cd /tmp/mt5install && \
    curl -L -o mt5setup.exe "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe" && \
    # Start Xvfb on display :99
    Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 & \
    XVFB_PID=$! && \
    export DISPLAY=:99 && \
    sleep 3 && \
    # Run MT5 installer with absolute path
    wine /tmp/mt5install/mt5setup.exe /auto > /tmp/mt5_install.log 2>&1 & \
    WINE_PID=$! && \
    # Wait for installation
    sleep 90 && \
    # Kill processes gracefully
    kill $WINE_PID 2>/dev/null || true && \
    wineserver -w && \
    kill $XVFB_PID 2>/dev/null || true && \
    # Find and copy MT5
    MT5_PATH=$(find /root/.wine/drive_c -name "terminal64.exe" -type f 2>/dev/null | head -1) && \
    echo "MT5 search result: $MT5_PATH" && \
    if [ -n "$MT5_PATH" ] && [ -f "$MT5_PATH" ]; then \
        MT5_DIR=$(dirname "$MT5_PATH") && \
        echo "Copying from: $MT5_DIR" && \
        cp -r "$MT5_DIR"/* /root/Metatrader/ && \
        echo "MT5 installed successfully"; \
    else \
        echo "WARNING: MT5 installation failed - terminal64.exe not found" && \
        echo "Install log:" && cat /tmp/mt5_install.log || true; \
    fi && \
    # Cleanup
    rm -rf /tmp/mt5install /tmp/mt5_install.log && \
    # Verify installation
    ls -la /root/Metatrader/ && \
    if [ -f "/root/Metatrader/terminal64.exe" ]; then \
        echo "SUCCESS: MT5 terminal64.exe found" ; \
    else \
        echo "ERROR: MT5 terminal64.exe NOT found" ; \
    fi




WORKDIR /root/

# # Copy healthcheck script
# COPY scripts/healthcheck.py /usr/local/bin/healthcheck.py
# RUN chmod +x /usr/local/bin/healthcheck.py

# # Configure healthcheck
# HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
#     CMD python3 /usr/local/bin/healthcheck.py || exit 1

EXPOSE 5900 2201 2202 2203 2204
CMD ["/usr/bin/supervisord","-c","/etc/supervisord.conf"]


