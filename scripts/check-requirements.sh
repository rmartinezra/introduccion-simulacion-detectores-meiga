#!/usr/bin/env bash
set -u

failures=0
warnings=0

check_command() {
  local command="$1" label="$2"
  if command -v "$command" >/dev/null 2>&1; then
    printf '[OK]   %-12s %s\n' "$label" "$(command -v "$command")"
  else
    printf '[FAIL] %-12s no encontrado\n' "$label"
    failures=$((failures + 1))
  fi
}

echo "MEIGA School — diagnóstico del estudiante"
check_command docker Docker
check_command python3 Python
check_command git Git

if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    echo "[OK]   Docker       daemon accesible desde WSL"
  else
    echo "[FAIL] Docker       daemon no accesible; active la integración WSL"
    failures=$((failures + 1))
  fi
  if docker inspect meiga_school >/dev/null 2>&1; then
    echo "[OK]   Container    meiga_school instalado"
  else
    echo "[WARN] Container    falta meiga_school"
    warnings=$((warnings + 1))
  fi
fi

if command -v python3 >/dev/null 2>&1; then
  if python3 -c 'import numpy, matplotlib' >/dev/null 2>&1; then
    echo "[OK]   Python libs  NumPy y Matplotlib disponibles"
  else
    echo "[WARN] Python libs  ejecute ./meiga-school setup"
    warnings=$((warnings + 1))
  fi
fi

memory_kib="$(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)"
cores="$(nproc 2>/dev/null || echo 0)"
free_gib="$(df -Pk . | awk 'NR==2 {printf "%.0f", $4/1024/1024}')"
echo "[INFO] Resources    ${cores} CPU, $((memory_kib / 1024 / 1024)) GiB RAM, ${free_gib} GiB libres"
if ((memory_kib < 8 * 1024 * 1024)); then
  echo "[WARN] Memory       se recomiendan al menos 8 GiB"
  warnings=$((warnings + 1))
fi
if ((free_gib < 15)); then
  echo "[WARN] Disk         se recomiendan al menos 15 GiB libres"
  warnings=$((warnings + 1))
fi

echo "Resultado: $failures fallos, $warnings advertencias"
exit "$failures"
