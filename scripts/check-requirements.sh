#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
IMAGE="${MEIGA_IMAGE:-rmartinezmaple/meiga-school:3.4.1-g4gro-viewer}"
CONTAINER_NAME="${MEIGA_CONTAINER:-meiga_school}"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"

failures=0
warnings=0

check_command() {
  local command_name="$1"
  local label="$2"
  if command -v "$command_name" >/dev/null 2>&1; then
    printf '[OK]   %-14s %s\n' "$label" "$(command -v "$command_name")"
  else
    printf '[FAIL] %-14s no encontrado\n' "$label"
    failures=$((failures + 1))
  fi
}

echo "MEIGA School — diagnóstico"
if [[ "$(uname -s 2>/dev/null)" != "Linux" ]]; then
  echo "[FAIL] Platform       se requiere Linux o WSL2"
  failures=$((failures + 1))
elif grep -qi microsoft /proc/sys/kernel/osrelease 2>/dev/null; then
  echo "[OK]   Platform       WSL2 ($(uname -m))"
else
  pretty_name="$(
    . /etc/os-release 2>/dev/null
    printf '%s' "${PRETTY_NAME:-Linux}"
  )"
  echo "[OK]   Platform       $pretty_name ($(uname -m))"
fi

check_command bash Bash
check_command docker Docker
check_command python3 Python
check_command git Git

if command -v python3 >/dev/null 2>&1; then
  if python3 -c 'import sys; raise SystemExit(not ((3, 10) <= sys.version_info < (3, 15)))'; then
    echo "[OK]   Python version $(python3 -c 'import sys; print(sys.version.split()[0])')"
  else
    echo "[FAIL] Python version se requiere Python 3.10-3.14"
    failures=$((failures + 1))
  fi
fi

if [[ -x "$VENV_PYTHON" ]] && \
  versions="$("$VENV_PYTHON" "$SCRIPT_DIR/verify-python-env.py" 2>/dev/null)"; then
  echo "[OK]   Python libs    ${versions#\[OK\] }"
else
  echo "[FAIL] Python libs    faltan o no coinciden con analysis/requirements.txt"
  echo "       Ejecute ./meiga-school install para repararlas."
  failures=$((failures + 1))
fi

if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    echo "[OK]   Docker daemon accesible"
  else
    echo "[FAIL] Docker daemon no accesible"
    if grep -qi microsoft /proc/sys/kernel/osrelease 2>/dev/null; then
      echo "       Inicie Docker Desktop y habilite la integración WSL."
    else
      echo "       Inicie Docker Engine y habilite acceso para su usuario."
    fi
    failures=$((failures + 1))
  fi

  if docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo "[OK]   Image          $IMAGE"
  else
    echo "[WARN] Image          falta $IMAGE"
    warnings=$((warnings + 1))
  fi

  if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
    if [[ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER_NAME")" != "true" ]]; then
      echo "[WARN] Container      $CONTAINER_NAME existe, pero está detenido"
      warnings=$((warnings + 1))
    elif docker exec "$CONTAINER_NAME" bash -lc \
      'test -x /opt/meiga-school/G4WCDSimulator/G4WCDSimulator &&
       test -x /usr/local/bin/meiga-viewer' >/dev/null 2>&1; then
      echo "[OK]   Container      $CONTAINER_NAME con WCD y visor 3D"
      if viewer_mapping="$(docker port "$CONTAINER_NAME" 6080/tcp 2>/dev/null)"; then
        echo "[OK]   Viewer port    ${viewer_mapping//$'\n'/, }"
      else
        echo "[FAIL] Viewer port    el contenedor no publica 6080/tcp"
        failures=$((failures + 1))
      fi
    else
      echo "[FAIL] Container      $CONTAINER_NAME no contiene el WCD esperado"
      failures=$((failures + 1))
    fi
  else
    echo "[WARN] Container      falta $CONTAINER_NAME"
    warnings=$((warnings + 1))
  fi
fi

memory_kib="$(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)"
cores="$(nproc 2>/dev/null || getconf _NPROCESSORS_ONLN 2>/dev/null || echo 0)"
free_gib="$(df -Pk "$PROJECT_ROOT" | awk 'NR==2 {printf "%.0f", $4/1024/1024}')"
echo "[INFO] Resources      ${cores} CPU, $((memory_kib / 1024 / 1024)) GiB RAM, ${free_gib} GiB libres"
if ((memory_kib < 8 * 1024 * 1024)); then
  echo "[WARN] Memory         se recomiendan al menos 8 GiB"
  warnings=$((warnings + 1))
fi
if ((free_gib < 15)); then
  echo "[WARN] Disk           se recomiendan al menos 15 GiB libres"
  warnings=$((warnings + 1))
fi

echo "Resultado: $failures fallos, $warnings advertencias"
exit "$failures"
