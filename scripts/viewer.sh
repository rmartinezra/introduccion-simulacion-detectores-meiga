#!/usr/bin/env bash

set -euo pipefail

DISPLAY_NUMBER=":1"
VNC_PORT="5901"
NOVNC_PORT="6080"

usage() {
    echo "Uso:"
    echo "  ./scripts/viewer.sh start ruta/al/archivo.wrl"
    echo "  ./scripts/viewer.sh stop"
}

stop_viewer() {
    pkill -f "view3dscene" 2>/dev/null || true
    pkill -f "websockify.*${NOVNC_PORT}" 2>/dev/null || true
    pkill -f "x11vnc.*${VNC_PORT}" 2>/dev/null || true
    pkill -f "fluxbox" 2>/dev/null || true
    pkill -f "Xvfb ${DISPLAY_NUMBER}" 2>/dev/null || true

    echo "[OK] Visualizador detenido."
}

start_viewer() {
    local wrl_file="${1:-}"

    if [[ -z "${wrl_file}" ]]; then
        echo "[ERROR] Debes indicar un archivo .wrl."
        usage
        exit 1
    fi

    if [[ ! -f "${wrl_file}" ]]; then
        echo "[ERROR] No existe el archivo: ${wrl_file}"
        exit 1
    fi

    wrl_file="$(realpath "${wrl_file}")"

    stop_viewer >/dev/null

    Xvfb "${DISPLAY_NUMBER}" \
        -screen 0 1280x900x24 \
        -ac \
        +extension GLX \
        +render \
        -noreset \
        >/tmp/meiga-xvfb.log 2>&1 &

    sleep 1

    DISPLAY="${DISPLAY_NUMBER}" fluxbox \
        >/tmp/meiga-fluxbox.log 2>&1 &

    x11vnc \
        -display "${DISPLAY_NUMBER}" \
        -forever \
        -shared \
        -nopw \
        -rfbport "${VNC_PORT}" \
        >/tmp/meiga-x11vnc.log 2>&1 &

    websockify \
        --web=/usr/share/novnc \
        "${NOVNC_PORT}" \
        "localhost:${VNC_PORT}" \
        >/tmp/meiga-novnc.log 2>&1 &

    DISPLAY="${DISPLAY_NUMBER}" view3dscene "${wrl_file}" \
        >/tmp/meiga-view3dscene.log 2>&1 &

    sleep 2

    echo "[OK] Visualizador iniciado."
    echo "[INFO] Archivo: ${wrl_file}"
    echo "[INFO] Abre el puerto 6080 y entra en /vnc.html"
}

case "${1:-}" in
    start)
        start_viewer "${2:-}"
        ;;
    stop)
        stop_viewer
        ;;
    *)
        usage
        exit 1
        ;;
esac