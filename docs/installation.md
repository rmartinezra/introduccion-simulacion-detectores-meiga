# Instalación en WSL y Linux

El proyecto necesita Bash y acceso administrativo mediante `sudo`. El
instalador prepara automáticamente Git, curl, Python 3.10–3.14, `venv` y Docker
cuando falten. Geant4, Boost y MEIGA permanecen dentro de la imagen.

## Windows con WSL2

1. Instale WSL2 y una distribución Ubuntu o Debian.
2. Obtenga el repositorio y ejecute:

```bash
./meiga-school install --pull
```

Si Docker no existe, el instalador instala Docker Engine dentro de WSL. Las
versiones recientes de Ubuntu instaladas con `wsl --install` usan systemd y
pueden iniciar el servicio directamente.

También puede usar Docker Desktop. Instálelo en Windows y habilite **Settings →
Resources → WSL Integration** para la distribución que utilizará. Si el
instalador detecta Docker Desktop, no instala un segundo Docker Engine.

Para mejor rendimiento, clone el repositorio dentro del sistema Linux
(`~/proyectos/...`) y no bajo `/mnt/c/...`.

### Docker Engine dentro de WSL

Si una distribución WSL antigua no está ejecutando systemd, actualice WSL y
habilítelo en `/etc/wsl.conf`:

```ini
[boot]
systemd=true
```

Después ejecute `wsl --shutdown` desde PowerShell, vuelva a abrir Ubuntu y
repita `./meiga-school install --pull`. Consulte la
[guía oficial de systemd en WSL](https://learn.microsoft.com/windows/wsl/systemd).

## Ubuntu y Debian nativos

Ejecute `./meiga-school install --pull`. El instalador usa los paquetes
mantenidos por la distribución e inicia Docker. Si necesita específicamente
Docker CE, puede instalarlo previamente siguiendo la guía oficial de
[Ubuntu](https://docs.docker.com/engine/install/ubuntu/) o
[Debian](https://docs.docker.com/engine/install/debian/); el script reutilizará
esa instalación.

## Fedora, RHEL y derivados

El instalador usa `dnf` y prepara `moby-engine`, Git, curl y Python. Si la
distribución no ofrece `moby-engine`, instale Docker Engine mediante la
[documentación oficial](https://docs.docker.com/engine/install/) y repita el
comando.

## Arch Linux

El instalador usa `pacman` para preparar Git, curl, Python y Docker, y después
inicia el servicio.

## openSUSE

El instalador usa `zypper` para preparar Git, curl, Python y Docker, y después
inicia el servicio.

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
  --image rmartinezmaple/meiga-school:3.3-g4gro
```

También se pueden fijar estos valores mediante `MEIGA_IMAGE`,
`MEIGA_CONTAINER` y `MEIGA_BUILD_JOBS`.

## Qué instala el comando

`./meiga-school install`:

1. detecta Linux/WSL y el gestor de paquetes;
2. instala Git, curl, Python, `venv`, certificados y Docker cuando falten;
3. inicia Docker y habilita al usuario actual;
4. crea `.venv` e instala las dependencias exactas del análisis;
5. descarga o reutiliza la imagen precompilada desde Docker Hub;
6. si hace falta, construye Geant4 10.7.4, Hodoscopio, Torre, WCD y G4GRO;
7. crea e inicia el contenedor `meiga_school`;
8. verifica que el ejecutable WCD esté disponible.

El proceso es idempotente y no elimina contenedores, imágenes ni resultados.
En sistemas administrados donde no deba instalar paquetes, utilice
`./meiga-school install --skip-system-deps`.

Las dependencias científicas se descargan únicamente como ruedas binarias. El
instalador usa NumPy 2.2.6 con Python 3.10 y NumPy 2.4.6 con Python 3.11–3.14;
no intenta compilar NumPy, Matplotlib ni sus extensiones en el computador.

## Entrar al contenedor

La imagen incluye `nano`, `vim`, `vi` y `less`. Abra una terminal Bash en
`/opt/meiga-school` con:

```bash
./meiga-school shell
```

Para salir sin detener el contenedor, ejecute `exit`. Si seleccionó otro nombre
durante la instalación, use `./meiga-school shell --container NOMBRE`.

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
