#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
VENV="$PROJECT_ROOT/.venv"

command -v python3 >/dev/null || { echo "[ERROR] Falta python3" >&2; exit 1; }
if [[ ! -d "$VENV" ]]; then
  python3 -m venv "$VENV" || {
    echo "[ERROR] No se pudo crear el entorno virtual. En Ubuntu instale: sudo apt install python3-venv" >&2
    exit 1
  }
fi
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install -r "$PROJECT_ROOT/analysis/requirements.txt"
echo "[OK] Entorno Python instalado en $VENV"
echo "     Active con: source .venv/bin/activate"
