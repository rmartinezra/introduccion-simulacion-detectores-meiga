#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

IMAGE="${MEIGA_IMAGE:-rmartinezmaple/meiga-school:3.4-g4gro-viewer}"
CONTAINER_NAME="${MEIGA_CONTAINER:-meiga_school}"
BUILD_JOBS="${MEIGA_BUILD_JOBS:-2}"
VIEWER_PORT="${MEIGA_VIEWER_PORT:-6080}"
IMAGE_MODE="auto"
FORCE_BUILD=0
INSTALL_PYTHON=1
INSTALL_SYSTEM_DEPS="${MEIGA_AUTO_INSTALL_SYSTEM:-1}"
ORIGINAL_ARGS=("$@")

usage() {
  cat <<'EOF'
Uso: ./meiga-school install [opciones]

Instala herramientas básicas, el entorno Python, la imagen y el contenedor.

Opciones:
  --image REFERENCIA   Imagen (default: rmartinezmaple/meiga-school:3.4-g4gro-viewer).
  --container NOMBRE   Nombre del contenedor (default: meiga_school).
  --jobs N             Núcleos para compilar Geant4/MEIGA (default: 2).
  --viewer-port N      Puerto local del visor 3D (default: 6080).
  --pull               Exige descargar --image; no usa el respaldo local.
  --build              Construye desde fuente en lugar de descargar.
  --force-build        Reconstruye la imagen aunque ya exista.
  --skip-python        No crea ni actualiza .venv.
  --skip-system-deps   No intenta instalar Git, Python ni Docker.
  -h, --help           Muestra esta ayuda.

Variables equivalentes: MEIGA_IMAGE, MEIGA_CONTAINER, MEIGA_BUILD_JOBS,
MEIGA_VIEWER_PORT y MEIGA_AUTO_INSTALL_SYSTEM (0 desactiva paquetes).
EOF
}

while (($#)); do
  case "$1" in
    --image) IMAGE="${2:?Falta REFERENCIA}"; shift 2 ;;
    --container) CONTAINER_NAME="${2:?Falta NOMBRE}"; shift 2 ;;
    --jobs) BUILD_JOBS="${2:?Falta N}"; shift 2 ;;
    --viewer-port) VIEWER_PORT="${2:?Falta N}"; shift 2 ;;
    --pull) IMAGE_MODE="pull"; shift ;;
    --build) IMAGE_MODE="build"; shift ;;
    --force-build) IMAGE_MODE="build"; FORCE_BUILD=1; shift ;;
    --skip-python) INSTALL_PYTHON=0; shift ;;
    --skip-system-deps) INSTALL_SYSTEM_DEPS=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[ERROR] Opción desconocida: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ "$BUILD_JOBS" =~ ^[1-9][0-9]*$ ]] || {
  echo "[ERROR] --jobs debe ser un entero positivo" >&2
  exit 2
}
[[ "$CONTAINER_NAME" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]] || {
  echo "[ERROR] Nombre de contenedor no válido: $CONTAINER_NAME" >&2
  exit 2
}
[[ "$VIEWER_PORT" =~ ^[1-9][0-9]*$ ]] &&
  ((VIEWER_PORT >= 1024 && VIEWER_PORT <= 65535)) || {
    echo "[ERROR] --viewer-port debe estar entre 1024 y 65535" >&2
    exit 2
  }

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "[ERROR] Ejecute este instalador desde Linux o WSL2." >&2
  exit 1
fi

if grep -qi microsoft /proc/sys/kernel/osrelease 2>/dev/null; then
  platform="WSL2"
else
  platform="Linux"
fi
echo "[INFO] Plataforma: $platform ($(uname -m))"

if ((INSTALL_SYSTEM_DEPS)); then
  bash "$SCRIPT_DIR/install-system-dependencies.sh"
fi

for command_name in bash docker python3; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "[ERROR] Falta '$command_name'. Consulte docs/installation.md." >&2
    exit 1
  }
done

# usermod no modifica los grupos suplementarios del proceso actual. Reejecutar
# solamente este instalador con el grupo docker permite continuar sin cerrar WSL.
if command -v sg >/dev/null 2>&1 && getent group docker >/dev/null 2>&1 && \
  [[ " $(id -nG) " != *" docker "* ]]; then
  docker_members="$(getent group docker | cut -d: -f4)"
  if [[ ",$docker_members," == *",${USER:-},"* ]]; then
    printf -v install_command '%q ' "$0" "${ORIGINAL_ARGS[@]}"
    echo "[INFO] Activando el grupo Docker para esta instalación..."
    exec sg docker -c "$install_command"
  fi
fi

python3 - <<'PY'
import sys
if not (sys.version_info >= (3, 10) and sys.version_info < (3, 15)):
    raise SystemExit(
        f"[ERROR] Se requiere Python 3.10-3.14; encontrado {sys.version.split()[0]}"
    )
print(f"[INFO] Python: {sys.version.split()[0]}")
PY

if ! docker info >/dev/null 2>&1; then
  if [[ "$platform" == "WSL2" ]]; then
    echo "[ERROR] Docker no responde." >&2
    echo "        Si usa Docker Desktop, ábralo y habilite la integración WSL." >&2
    echo "        Si instaló Docker Engine, compruebe que WSL utiliza systemd." >&2
  else
    echo "[ERROR] Docker no responde. Inicie Docker Engine y habilite acceso para su usuario." >&2
  fi
  exit 1
fi

if ((INSTALL_PYTHON)); then
  "$SCRIPT_DIR/setup-python.sh"
fi

image_available=0
if docker image inspect "$IMAGE" >/dev/null 2>&1; then
  image_available=1
fi

if [[ "$IMAGE_MODE" == "pull" ]]; then
  echo "[INFO] Descargando imagen $IMAGE..."
  docker pull "$IMAGE"
elif [[ "$IMAGE_MODE" == "auto" ]] && ((image_available == 0)); then
  echo "[INFO] Descargando imagen precompilada $IMAGE..."
  if ! docker pull "$IMAGE"; then
    echo "[WARN] No se pudo descargar; se construirá desde fuente." >&2
    IMAGE_MODE="build"
  fi
fi

if [[ "$IMAGE_MODE" == "build" ]] && \
  { ((FORCE_BUILD)) || ((image_available == 0)); }; then
    echo "[INFO] Construyendo $IMAGE desde Ubuntu 22.04 y Geant4 10.7.4."
    echo "[INFO] La primera construcción puede tardar varios minutos."
    docker build \
      --file "$PROJECT_ROOT/container/Dockerfile" \
      --tag "$IMAGE" \
      --build-arg "BUILD_JOBS=$BUILD_JOBS" \
      "$PROJECT_ROOT"
elif docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "[OK] Imagen disponible: $IMAGE"
else
  echo "[ERROR] No se pudo preparar la imagen $IMAGE" >&2
  exit 1
fi

if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
  container_image_id="$(docker inspect -f '{{.Image}}' "$CONTAINER_NAME")"
  requested_image_id="$(docker image inspect -f '{{.Id}}' "$IMAGE")"
  if [[ "$container_image_id" != "$requested_image_id" ]]; then
    echo "[ERROR] El contenedor '$CONTAINER_NAME' pertenece a otra versión de la imagen." >&2
    echo "        Se conservó intacto. Use, por ejemplo:" >&2
    echo "        ./meiga-school install --container ${CONTAINER_NAME}_new" >&2
    exit 1
  fi
  echo "[INFO] Reutilizando el contenedor existente: $CONTAINER_NAME"
  viewer_mapping="$(docker port "$CONTAINER_NAME" 6080/tcp 2>/dev/null || true)"
  if [[ "$viewer_mapping" != "127.0.0.1:${VIEWER_PORT}" ]]; then
    echo "[ERROR] El contenedor existente no usa el puerto solicitado para el visor." >&2
    echo "        Actual: ${viewer_mapping:-sin publicar}; solicitado: 127.0.0.1:${VIEWER_PORT}" >&2
    echo "        Se conservó intacto. Cree otro contenedor, por ejemplo:" >&2
    echo "        ./meiga-school install --container ${CONTAINER_NAME}_viewer" >&2
    exit 1
  fi
else
  docker create \
    --name "$CONTAINER_NAME" \
    --init \
    --label "org.meiga-school.managed=true" \
    --publish "127.0.0.1:${VIEWER_PORT}:6080" \
    "$IMAGE" >/dev/null
  echo "[OK] Contenedor creado: $CONTAINER_NAME"
fi

if [[ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER_NAME")" != "true" ]]; then
  docker start "$CONTAINER_NAME" >/dev/null
fi

if ! docker exec "$CONTAINER_NAME" \
  test -x /opt/meiga-school/G4WCDSimulator/G4WCDSimulator; then
  echo "[ERROR] '$CONTAINER_NAME' existe pero no contiene el WCD de MEIGA." >&2
  echo "        Use --container con otro nombre o revise docs/installation.md." >&2
  exit 1
fi

PYTHON="$PROJECT_ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "[ERROR] No existe $PYTHON." >&2
  echo "        Quite --skip-python o ejecute ./scripts/setup-python.sh." >&2
  exit 1
fi
"$PYTHON" "$SCRIPT_DIR/verify-python-env.py"

echo "[OK] Instalación lista."
echo "     Primera prueba: ./meiga-school run wcd-30s --smoke 60"
