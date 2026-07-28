FROM mcr.microsoft.com/devcontainers/universal:2

USER root

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
        view3dscene \
        xvfb \
        x11vnc \
        fluxbox \
        novnc \
        websockify \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER codespace