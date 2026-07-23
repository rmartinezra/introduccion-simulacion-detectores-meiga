# Instalación en WSL y Linux

El proyecto necesita solamente Git, Bash, Python 3.10+ y un Docker funcional en
el sistema anfitrión. Geant4, Boost y MEIGA se construyen dentro de la imagen.

## Windows con WSL2

1. Instale WSL2 y una distribución Ubuntu o Debian.
2. Instale Docker Desktop para Windows.
3. En Docker Desktop, habilite **Settings → Resources → WSL Integration** para
   la distribución que utilizará.
4. Abra la terminal WSL y verifique:

```bash
docker info
python3 --version
git --version
```

Para mejor rendimiento, clone el repositorio dentro del sistema Linux
(`~/proyectos/...`) y no bajo `/mnt/c/...`.

En Ubuntu dentro de WSL, si faltan Git, Python o `venv`:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv
```

No instale un segundo daemon Docker dentro de WSL cuando use Docker Desktop.

## Ubuntu y Debian nativos

Instale las herramientas del anfitrión:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv
```

Instale Docker Engine siguiendo la guía oficial correspondiente a
[Ubuntu](https://docs.docker.com/engine/install/ubuntu/) o
[Debian](https://docs.docker.com/engine/install/debian/). Después compruebe que
su usuario puede ejecutar:

```bash
docker info
```

## Fedora, RHEL y derivados

```bash
sudo dnf install -y git python3
```

Instale Docker Engine mediante la
[documentación oficial](https://docs.docker.com/engine/install/) para su
distribución. El instalador del curso no depende de `apt`.

## Arch Linux

```bash
sudo pacman -S --needed git python docker
sudo systemctl enable --now docker
```

Configure el acceso de su usuario a Docker según la documentación de Arch y
verifique `docker info`.

## openSUSE

```bash
sudo zypper install git python3 python3-pip docker
sudo systemctl enable --now docker
```

Verifique que `python3 -m venv --help` y `docker info` funcionen.

## Instalar el curso

```bash
git clone https://github.com/rmartinezra/introduccion-simulacion-detectores-meiga.git
cd introduccion-simulacion-detectores-meiga
./meiga-school install
```

Por defecto se usan dos núcleos para evitar agotar la memoria durante la
compilación de respaldo. Para exigir una construcción local en un equipo con
suficiente RAM:

```bash
./meiga-school install --build --jobs 4 --force-build
```

La imagen pública predeterminada es:

```bash
./meiga-school install \
  --pull \
  --image rmartinezmaple/meiga-school:3.2-g4gro
```

También se pueden fijar estos valores mediante `MEIGA_IMAGE`,
`MEIGA_CONTAINER` y `MEIGA_BUILD_JOBS`.

## Qué instala el comando

`./meiga-school install`:

1. valida Linux/WSL, Docker y Python;
2. crea `.venv` e instala las dependencias del análisis;
3. descarga o reutiliza la imagen precompilada desde Docker Hub;
4. si hace falta, construye Geant4 10.7.4, Hodoscopio, Torre, WCD y G4GRO;
5. crea e inicia el contenedor `meiga_school`;
6. verifica que el ejecutable WCD esté disponible.

El proceso es idempotente y no elimina contenedores, imágenes ni resultados.

## Contenedor con el mismo nombre

Si ya existe un contenedor llamado `meiga_school`, el instalador lo conserva.
Si pertenece a otra versión de la imagen, el instalador se detiene para no
reemplazarlo ni perder cambios. Utilice otro nombre:

```bash
./meiga-school install --container meiga_school_curso
MEIGA_CONTAINER=meiga_school_curso \
  ./meiga-school run wcd-30s --smoke 60
```

## Diagnóstico

```bash
./meiga-school doctor
```

Problemas frecuentes:

- **Docker no responde en WSL:** inicie Docker Desktop y habilite WSL
  Integration.
- **Permission denied en Linux:** configure el acceso de su usuario al daemon
  Docker y abra una nueva sesión.
- **No se puede crear `.venv`:** instale el módulo `venv` de su distribución.
- **Poca memoria:** use `--jobs 1`.
- **Poco espacio:** libere al menos 15 GiB antes de construir la imagen.
