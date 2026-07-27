#!/usr/bin/env bash
set -Eeuo pipefail

is_wsl=0
if grep -qi microsoft /proc/sys/kernel/osrelease 2>/dev/null; then
  is_wsl=1
fi

if ((EUID == 0)); then
  SUDO=()
  target_user="${SUDO_USER:-root}"
elif command -v sudo >/dev/null 2>&1; then
  SUDO=(sudo)
  target_user="${USER:?No se pudo determinar el usuario actual}"
else
  echo "[ERROR] Faltan dependencias del sistema y no está disponible 'sudo'." >&2
  echo "        Inicie sesión como administrador o instale sudo." >&2
  exit 1
fi

docker_desktop_detected=0
if ((is_wsl)) && {
  [[ -e "/mnt/c/Program Files/Docker/Docker/Docker Desktop.exe" ]] ||
  command -v docker.exe >/dev/null 2>&1
}; then
  docker_desktop_detected=1
fi

need_packages=0
for command_name in curl git python3; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    need_packages=1
  fi
done
if command -v python3 >/dev/null 2>&1 && \
  ! python3 -c 'import ensurepip, venv' >/dev/null 2>&1; then
  need_packages=1
fi
if ! command -v docker >/dev/null 2>&1 && ((docker_desktop_detected == 0)); then
  need_packages=1
fi

if ((need_packages)); then
  echo "[INFO] Instalando herramientas básicas del sistema..."
  if command -v apt-get >/dev/null 2>&1; then
    packages=(ca-certificates curl git python3 python3-venv)
    if ! command -v docker >/dev/null 2>&1 && ((docker_desktop_detected == 0)); then
      packages+=(docker.io)
    fi
    "${SUDO[@]}" apt-get update
    "${SUDO[@]}" env DEBIAN_FRONTEND=noninteractive \
      apt-get install -y "${packages[@]}"
  elif command -v dnf >/dev/null 2>&1; then
    packages=(ca-certificates curl git python3 python3-pip)
    if ! command -v docker >/dev/null 2>&1; then
      packages+=(moby-engine)
    fi
    "${SUDO[@]}" dnf install -y "${packages[@]}"
  elif command -v pacman >/dev/null 2>&1; then
    packages=(ca-certificates curl git python docker)
    "${SUDO[@]}" pacman -S --needed --noconfirm "${packages[@]}"
  elif command -v zypper >/dev/null 2>&1; then
    packages=(ca-certificates curl git python3 python3-pip docker)
    "${SUDO[@]}" zypper --non-interactive install "${packages[@]}"
  else
    echo "[ERROR] No se reconoce el gestor de paquetes de esta distribución." >&2
    echo "        Consulte docs/installation.md para instalar Docker, Git y Python." >&2
    exit 1
  fi
fi

if ! command -v docker >/dev/null 2>&1; then
  if ((docker_desktop_detected)); then
    echo "[ERROR] Docker Desktop está instalado, pero esta distribución WSL no tiene integración." >&2
    echo "        Abra Docker Desktop y habilite Settings > Resources > WSL Integration." >&2
  else
    echo "[ERROR] No se pudo instalar el comando Docker." >&2
    echo "        Consulte docs/installation.md para su distribución." >&2
  fi
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  if command -v systemctl >/dev/null 2>&1 && \
    [[ "$(ps -p 1 -o comm= 2>/dev/null | tr -d ' ')" == "systemd" ]] && \
    systemctl list-unit-files docker.service >/dev/null 2>&1; then
    echo "[INFO] Iniciando Docker Engine..."
    "${SUDO[@]}" systemctl enable --now docker
  elif command -v service >/dev/null 2>&1 && [[ -e /etc/init.d/docker ]]; then
    echo "[INFO] Iniciando Docker Engine..."
    "${SUDO[@]}" service docker start
  elif ((is_wsl)) && [[ -e /lib/systemd/system/docker.service ]]; then
    echo "[WARN] Docker Engine está instalado, pero WSL no está ejecutando systemd." >&2
    echo "       Consulte la sección 'Docker Engine dentro de WSL' en docs/installation.md." >&2
  fi
fi

if getent group docker >/dev/null 2>&1 && [[ "$target_user" != "root" ]]; then
  docker_members="$(getent group docker | cut -d: -f4)"
  if [[ ",$docker_members," != *",$target_user,"* ]]; then
    echo "[INFO] Habilitando Docker para el usuario '$target_user'..."
    "${SUDO[@]}" usermod -aG docker "$target_user"
  fi
fi

for command_name in curl git python3 docker; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "[ERROR] No quedó disponible '$command_name'." >&2
    exit 1
  }
done
python3 -c 'import ensurepip, venv' >/dev/null 2>&1 || {
  echo "[ERROR] Python no incluye los módulos ensurepip y venv." >&2
  exit 1
}

echo "[OK] Dependencias básicas disponibles."
