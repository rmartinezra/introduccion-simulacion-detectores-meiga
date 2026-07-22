#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
ANALYZER="$PROJECT_ROOT/analysis/wcd/analyze_wcd.py"
RESULTS_ROOT="$PROJECT_ROOT/results/runs"

EXPERIMENT=""
CONTAINER_NAME="${MEIGA_CONTAINER:-meiga_school}"
SEED=2026072230
SCENARIOS="all"
MAX_PARTICLES=0
RUN_ID=""
BUILD_FIRST=1

usage() {
  cat <<'EOF'
Uso: scripts/run-wcd-campaign.sh --experiment DIRECTORIO [opciones]

Opciones:
  --components        Simula también EM, muones y hadrones por separado.
  --smoke N           Prueba rápida estratificada con N partículas.
  --seed N            Semilla positiva de Geant4.
  --run-id NOMBRE     Identificador de salida (por defecto se genera solo).
  --container NOMBRE  Contenedor Docker (default: meiga_school).
  --no-build          No recompila G4WCDSimulator antes de simular.
  -h, --help          Muestra esta ayuda.
EOF
}

while (($#)); do
  case "$1" in
    --experiment) EXPERIMENT="${2:?Falta DIRECTORIO}"; shift 2 ;;
    --components) SCENARIOS="all,electromagnetic,muonic,hadronic"; shift ;;
    --smoke) MAX_PARTICLES="${2:?Falta N}"; shift 2 ;;
    --seed) SEED="${2:?Falta N}"; shift 2 ;;
    --run-id) RUN_ID="${2:?Falta NOMBRE}"; shift 2 ;;
    --container) CONTAINER_NAME="${2:?Falta NOMBRE}"; shift 2 ;;
    --no-build) BUILD_FIRST=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[ERROR] Opción desconocida: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ -n "$EXPERIMENT" ]] || { echo "[ERROR] Falta --experiment" >&2; exit 2; }
EXPERIMENT="$(cd -- "$EXPERIMENT" && pwd)"
[[ -f "$EXPERIMENT/campaign.json" ]] || { echo "[ERROR] Falta campaign.json" >&2; exit 1; }
[[ "$SEED" =~ ^[1-9][0-9]*$ ]] || { echo "[ERROR] --seed debe ser positivo" >&2; exit 2; }
[[ "$MAX_PARTICLES" =~ ^[0-9]+$ ]] || { echo "[ERROR] --smoke debe ser entero" >&2; exit 2; }

command -v docker >/dev/null || { echo "[ERROR] Docker no está disponible dentro de WSL" >&2; exit 1; }
command -v python3 >/dev/null || { echo "[ERROR] Falta python3" >&2; exit 1; }
python3 -c 'import numpy, matplotlib' >/dev/null 2>&1 || {
  echo "[ERROR] Ejecute primero: ./meiga-school setup" >&2
  exit 1
}

readarray -t metadata < <(
  python3 - "$EXPERIMENT/campaign.json" <<'PY'
import json, re, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
slug = re.sub(r"[^A-Za-z0-9._-]+", "-", data["name"]).strip("-")
print(slug)
print(float(data["duration_s"]))
print(float(data["injection_area"]["radius_m"]))
print(float(data["analysis"]["acquisition_window_ns"]))
PY
)
CAMPAIGN_SLUG="${metadata[0]}"
DURATION="${metadata[1]}"
INJECTION_RADIUS="${metadata[2]}"
ACQUISITION_WINDOW="${metadata[3]}"

if [[ -z "$RUN_ID" ]]; then
  if ((MAX_PARTICLES > 0)); then
    RUN_ID="${CAMPAIGN_SLUG}-smoke-${MAX_PARTICLES}-seed-${SEED}"
  else
    RUN_ID="${CAMPAIGN_SLUG}-seed-${SEED}"
  fi
fi
[[ "$RUN_ID" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "[ERROR] --run-id no es seguro" >&2; exit 2; }

RUN_DIR="$RESULTS_ROOT/$RUN_ID/run"
ANALYSIS_DIR="$RESULTS_ROOT/$RUN_ID/analysis"
PLOT_DIR="$RESULTS_ROOT/$RUN_ID/plots"
[[ ! -e "$RESULTS_ROOT/$RUN_ID" ]] || { echo "[ERROR] Ya existe $RESULTS_ROOT/$RUN_ID" >&2; exit 1; }

if ! docker inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
  echo "[ERROR] No existe el contenedor '$CONTAINER_NAME'" >&2
  exit 1
fi
if [[ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER_NAME")" != "true" ]]; then
  docker start "$CONTAINER_NAME" >/dev/null
fi

if ((BUILD_FIRST)) && docker exec "$CONTAINER_NAME" test -d /opt/meiga-dev-build; then
  echo "[INFO] Compilando G4WCDSimulator..."
  docker exec "$CONTAINER_NAME" cmake --build /opt/meiga-dev-build --target G4WCDSimulator --parallel 2
fi

EXECUTABLE=""
for candidate in \
  /opt/meiga-dev-build/Applications/G4WCDSimulator/G4WCDSimulator \
  /opt/meiga-school/G4WCDSimulator/G4WCDSimulator \
  /opt/meiga/build/Applications/G4WCDSimulator/G4WCDSimulator; do
  if docker exec "$CONTAINER_NAME" test -x "$candidate"; then
    EXECUTABLE="$candidate"
    break
  fi
done
[[ -n "$EXECUTABLE" ]] || { echo "[ERROR] No se encontró G4WCDSimulator" >&2; exit 1; }

mkdir -p "$RUN_DIR" "$ANALYSIS_DIR" "$PLOT_DIR"
python3 "$ANALYZER" prepare --experiment "$EXPERIMENT" --run-dir "$RUN_DIR" \
  --scenarios "$SCENARIOS" --seed "$SEED" --max-particles "$MAX_PARTICLES"

CONTAINER_RUN="/tmp/meiga-school-${RUN_ID}"
case "$CONTAINER_RUN" in /tmp/meiga-school-*) ;; *) echo "[ERROR] Ruta temporal insegura" >&2; exit 1 ;; esac
docker exec "$CONTAINER_NAME" mkdir -p "$CONTAINER_RUN"
docker cp "$RUN_DIR/." "$CONTAINER_NAME:$CONTAINER_RUN/"

cleanup() {
  case "$CONTAINER_RUN" in
    /tmp/meiga-school-*) docker exec "$CONTAINER_NAME" rm -rf -- "$CONTAINER_RUN" >/dev/null 2>&1 || true ;;
  esac
}
trap cleanup EXIT

IFS=',' read -r -a scenario_list <<< "$SCENARIOS"
for scenario in "${scenario_list[@]}"; do
  echo "[INFO] Simulando $scenario..."
  docker exec "$CONTAINER_NAME" bash -lc \
    "cd '$CONTAINER_RUN/scenarios/$scenario' && '$EXECUTABLE' -c config.json > run.log 2>&1"
done

docker cp "$CONTAINER_NAME:$CONTAINER_RUN/." "$RUN_DIR/"
EXECUTABLE_SHA256="$(docker exec "$CONTAINER_NAME" sha256sum "$EXECUTABLE" | awk '{print $1}')"

mapfile -d '' wrl_files < <(find "$RUN_DIR/scenarios" -type f -name '*.wrl' -print0)
if ((${#wrl_files[@]} != 1)); then
  echo "[ERROR] Se esperaba exactamente un archivo WRL; se encontraron ${#wrl_files[@]}" >&2
  exit 1
fi
[[ -s "${wrl_files[0]}" ]] || { echo "[ERROR] El archivo WRL está vacío" >&2; exit 1; }
mv -- "${wrl_files[0]}" "$RUN_DIR/visualization.wrl"

python3 "$ANALYZER" analyze --run-dir "$RUN_DIR" --analysis-dir "$ANALYSIS_DIR" \
  --plot-dir "$PLOT_DIR" --duration "$DURATION" --injection-radius "$INJECTION_RADIUS" \
  --acquisition-window "$ACQUISITION_WINDOW" --executable "$EXECUTABLE" \
  --executable-sha256 "$EXECUTABLE_SHA256"

echo "[OK] Corrida:  $RESULTS_ROOT/$RUN_ID"
echo "[OK] Figuras:  $PLOT_DIR (PNG + PDF)"
echo "[OK] VRML:     $RUN_DIR/visualization.wrl"
