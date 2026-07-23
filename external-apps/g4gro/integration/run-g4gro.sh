#!/usr/bin/env bash
set -Eeuo pipefail

PREFIX="/opt/meiga-school/external/G4GROSimulator"
VENDOR="$PREFIX/vendor/Escuela/G4GROSimulator"
EXECUTABLE="$PREFIX/build/Applications/G4GROSimulator/G4GROSimulator"
MODE="${1:-smoke}"
RUN_ID="${2:-$(date -u +%Y%m%dT%H%M%SZ)-$MODE}"

case "$MODE" in
  smoke) INPUT="$VENDOR/all_neutrons.shw" ;;
  practice) INPUT="$VENDOR/practica.shw" ;;
  full) INPUT="$VENDOR/bga_30_segundos.shw" ;;
  muon) INPUT="$VENDOR/vertical_muon.txt" ;;
  *) echo "Uso: $0 {smoke|practice|full|muon} [run-id]" >&2; exit 2 ;;
esac
[[ "$RUN_ID" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "[ERROR] run-id no seguro" >&2; exit 2; }
[[ -x "$EXECUTABLE" ]] || { echo "[ERROR] Falta el ejecutable aislado: $EXECUTABLE" >&2; exit 1; }

RUN_DIR="$PREFIX/runs/$RUN_ID"
[[ ! -e "$RUN_DIR" ]] || { echo "[ERROR] Ya existe $RUN_DIR" >&2; exit 1; }
mkdir -p "$RUN_DIR"
cp "$INPUT" "$RUN_DIR/input.shw"
cp "$VENDOR/DetectorList.xml" "$RUN_DIR/DetectorList.xml"
cp "$PREFIX/runtime/DetectorProperties.xml" "$RUN_DIR/DetectorProperties.xml"
cp "$PREFIX/runtime/G4GROSimulator.json" "$RUN_DIR/G4GROSimulator.json"

echo "[INFO] G4GRO mode=$MODE run=$RUN_DIR"
(
  cd "$RUN_DIR"
  "$EXECUTABLE" -c G4GROSimulator.json > run.log 2>&1
)
echo "[OK] $RUN_DIR"
find "$RUN_DIR" -maxdepth 1 -type f -printf '%f %s bytes\n' | sort
