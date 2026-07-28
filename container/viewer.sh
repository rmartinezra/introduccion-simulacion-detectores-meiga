#!/usr/bin/env bash
set -Eeuo pipefail

readonly STATE_DIR="/tmp/meiga-viewer"
readonly INPUT_DIR="$STATE_DIR/input"
readonly DISPLAY_NAME=":91"
readonly DISPLAY_SOCKET="/tmp/.X11-unix/X91"
readonly VNC_PORT="5901"
readonly WEB_PORT="6080"
readonly WEB_ROOT="/usr/share/novnc"

usage() {
  cat <<'EOF'
Usage:
  meiga-viewer start FILE.wrl
  meiga-viewer stop
  meiga-viewer status
EOF
}

pid_is_running() {
  local pid_file="$1"
  local pid=""
  [[ -s "$pid_file" ]] || return 1
  pid="$(<"$pid_file")"
  [[ "$pid" =~ ^[1-9][0-9]*$ ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

stop_process() {
  local name="$1"
  local pid_file="$STATE_DIR/$name.pid"
  local pid=""

  if [[ -s "$pid_file" ]]; then
    pid="$(<"$pid_file")"
  fi
  if [[ "$pid" =~ ^[1-9][0-9]*$ ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    for _ in {1..20}; do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.1
    done
    if kill -0 "$pid" 2>/dev/null; then
      kill -KILL "$pid" 2>/dev/null || true
    fi
  fi
  rm -f -- "$pid_file"
}

stop_all() {
  mkdir -p "$STATE_DIR"
  stop_process view3dscene
  stop_process websockify
  stop_process x11vnc
  stop_process fluxbox
  stop_process xvfb
}

start_background() {
  local name="$1"
  shift
  nohup "$@" >"$STATE_DIR/$name.log" 2>&1 </dev/null &
  printf '%s\n' "$!" >"$STATE_DIR/$name.pid"
}

show_start_failure() {
  local log=""
  echo "[ERROR] The 3D viewer could not be started." >&2
  for log in xvfb fluxbox x11vnc websockify view3dscene; do
    if [[ -s "$STATE_DIR/$log.log" ]]; then
      echo "----- $log.log -----" >&2
      tail -n 20 "$STATE_DIR/$log.log" >&2
    fi
  done
}

start_viewer() {
  local requested_file="${1:-}"
  local vrml_file=""
  local startup_ok=0

  [[ -n "$requested_file" ]] || {
    echo "[ERROR] Missing VRML file." >&2
    usage >&2
    return 2
  }
  vrml_file="$(realpath -e -- "$requested_file")" || {
    echo "[ERROR] VRML file does not exist: $requested_file" >&2
    return 1
  }
  [[ -f "$vrml_file" && -s "$vrml_file" ]] || {
    echo "[ERROR] VRML file is not a non-empty regular file: $vrml_file" >&2
    return 1
  }
  [[ "${vrml_file,,}" == *.wrl ]] || {
    echo "[ERROR] Expected a .wrl file: $vrml_file" >&2
    return 1
  }

  for command_name in Xvfb fluxbox x11vnc websockify view3dscene curl; do
    command -v "$command_name" >/dev/null 2>&1 || {
      echo "[ERROR] Missing viewer command: $command_name" >&2
      return 1
    }
  done
  [[ -f "$WEB_ROOT/vnc.html" ]] || {
    echo "[ERROR] noVNC web client not found at $WEB_ROOT/vnc.html" >&2
    return 1
  }

  mkdir -p "$STATE_DIR" "$INPUT_DIR"
  stop_all
  trap '
    status=$?
    if ((status != 0 && startup_ok == 0)); then
      show_start_failure
      stop_all
    fi
  ' EXIT

  start_background xvfb \
    Xvfb "$DISPLAY_NAME" -screen 0 1280x900x24 -ac -nolisten tcp
  for _ in {1..50}; do
    [[ -S "$DISPLAY_SOCKET" ]] && break
    pid_is_running "$STATE_DIR/xvfb.pid" || return 1
    sleep 0.1
  done
  [[ -S "$DISPLAY_SOCKET" ]] || return 1

  start_background fluxbox \
    env DISPLAY="$DISPLAY_NAME" fluxbox
  start_background x11vnc \
    x11vnc \
      -display "$DISPLAY_NAME" \
      -forever \
      -shared \
      -nopw \
      -localhost \
      -noxdamage \
      -rfbport "$VNC_PORT"
  for _ in {1..50}; do
    grep -q "PORT=$VNC_PORT" "$STATE_DIR/x11vnc.log" 2>/dev/null && break
    pid_is_running "$STATE_DIR/x11vnc.pid" || return 1
    sleep 0.1
  done
  grep -q "PORT=$VNC_PORT" "$STATE_DIR/x11vnc.log" || return 1

  start_background websockify \
    websockify --web="$WEB_ROOT" "$WEB_PORT" "127.0.0.1:$VNC_PORT"
  for _ in {1..50}; do
    curl --fail --silent --output /dev/null \
      "http://127.0.0.1:$WEB_PORT/vnc.html" && break
    pid_is_running "$STATE_DIR/websockify.pid" || return 1
    sleep 0.1
  done
  curl --fail --silent --output /dev/null \
    "http://127.0.0.1:$WEB_PORT/vnc.html" || return 1

  start_background view3dscene \
    env \
      DISPLAY="$DISPLAY_NAME" \
      LIBGL_ALWAYS_SOFTWARE=1 \
      view3dscene "$vrml_file"
  sleep 1
  pid_is_running "$STATE_DIR/view3dscene.pid" || return 1

  printf '%s\n' "$vrml_file" >"$STATE_DIR/current-file"
  startup_ok=1
  trap - EXIT
  echo "[OK] 3D viewer started for $vrml_file"
  echo "[OK] noVNC is listening on container port $WEB_PORT"
}

viewer_status() {
  if pid_is_running "$STATE_DIR/view3dscene.pid" &&
    pid_is_running "$STATE_DIR/websockify.pid"; then
    echo "[OK] 3D viewer is running."
    if [[ -s "$STATE_DIR/current-file" ]]; then
      echo "     File: $(<"$STATE_DIR/current-file")"
    fi
    echo "     Container port: $WEB_PORT"
    return 0
  fi
  echo "[INFO] 3D viewer is stopped."
  return 1
}

command_name="${1:-}"
case "$command_name" in
  start)
    shift
    start_viewer "${1:-}"
    ;;
  stop)
    stop_all
    rm -f -- "$STATE_DIR/current-file"
    echo "[OK] 3D viewer stopped."
    ;;
  status)
    viewer_status
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "[ERROR] Unknown viewer command: ${command_name:-<empty>}" >&2
    usage >&2
    exit 2
    ;;
esac
