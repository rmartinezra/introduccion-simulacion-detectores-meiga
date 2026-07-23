#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
VENV="$PROJECT_ROOT/.venv"

command -v python3 >/dev/null || { echo "[ERROR] Falta python3" >&2; exit 1; }
python3 - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit(
        f"[ERROR] Se requiere Python >= 3.10; encontrado {sys.version.split()[0]}"
    )
PY

if [[ ! -d "$VENV" ]]; then
  python3 -m venv "$VENV" || {
    echo "[ERROR] No se pudo crear .venv. Instale el paquete venv de su distribución." >&2
    echo "        Debian/Ubuntu: sudo apt install python3-venv" >&2
    exit 1
  }
fi
"$VENV/bin/python" -m pip install --disable-pip-version-check --upgrade pip
"$VENV/bin/python" -m pip install \
  --disable-pip-version-check \
  -r "$PROJECT_ROOT/analysis/requirements.txt"
"$VENV/bin/python" - <<'PY'
import matplotlib
import numpy
print(f"[OK] NumPy {numpy.__version__}; Matplotlib {matplotlib.__version__}")
PY
echo "[OK] Entorno Python instalado en $VENV"
echo "     Los comandos ./meiga-school lo usarán automáticamente."
