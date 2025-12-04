# MetaTrader 5 Docker Image - Debian 13 (Trixie) with Wine 10.x
FROM debian:trixie-slim

USER root
ENV WINEPREFIX=/config/.wine
ENV WINEARCH=win64
ENV DISPLAY=:0
ENV DEBIAN_FRONTEND=noninteractive
ENV MT5_INSTALLER_URL=https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe

# Install basic dependencies
RUN apt-get update && apt-get install -y \
    wget curl gnupg2 \
    ca-certificates apt-transport-https \
    && rm -rf /var/lib/apt/lists/*

# Add WineHQ repository for Wine 10.x
RUN dpkg --add-architecture i386 && \
    mkdir -pm755 /etc/apt/keyrings && \
    wget -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key && \
    wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/debian/dists/trixie/winehq-trixie.sources

# Install Wine 10.x (stable or staging)
RUN apt-get update && apt-get install -y \
    --install-recommends winehq-stable \
    && rm -rf /var/lib/apt/lists/*

# Install X11 and VNC server
RUN apt-get update && apt-get install -y \
    xvfb x11vnc xorg openbox \
    x11-utils x11-xserver-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python 3 and pyzmq
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    libzmq5 libzmq3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir pyzmq

# Setup Python environment
ENV PATH="/opt/venv/bin:$PATH"

# Create directories
RUN mkdir -p /config /scripts

# Copy scripts
COPY scripts/start-mt5.sh /scripts/start-mt5.sh
COPY scripts/mt5-watchdog.sh /scripts/mt5-watchdog.sh
COPY scripts/health-check.sh /scripts/health-check.sh
RUN chmod +x /scripts/*.sh

WORKDIR /root

EXPOSE 5900 2201 2202 2203 2204

CMD ["/scripts/start-mt5.sh"]
