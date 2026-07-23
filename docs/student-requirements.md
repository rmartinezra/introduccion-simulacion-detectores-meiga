# Requisitos para estudiantes

## Plataforma mínima

- Windows 10/11 de 64 bits con WSL2, o Linux de 64 bits.
- Docker Desktop con integración WSL2, o Docker Engine nativo.
- Bash, Git y Python 3.10 o posterior.
- 4 núcleos, 8 GiB de RAM y 15 GiB libres.

Se admiten Ubuntu, Debian, Fedora/RHEL, Arch Linux, openSUSE y distribuciones
equivalentes. El sistema anfitrión no necesita Geant4, CMake ni Boost.

## Configuración recomendada

- 8 núcleos, 16 GiB de RAM y 30 GiB libres.
- En WSL, guardar el repositorio dentro de `~/...` y no en `/mnt/c/...`.
- Usar dos trabajos de compilación con 8 GiB y cuatro con 16 GiB o más.

No se requiere GPU.

## Instalación

Después de instalar Docker, Git y Python:

```bash
git clone https://github.com/rmartinezra/introduccion-simulacion-detectores-meiga.git
cd introduccion-simulacion-detectores-meiga
./meiga-school install
```

El comando instala NumPy 2.2.6 y Matplotlib 3.10.3 dentro de `.venv`; no
modifica el Python del sistema. La imagen de simulación se descarga de Docker
Hub; no es necesario compilar Geant4 en el equipo del estudiante.

Consulte [installation.md](installation.md) para instrucciones por
distribución.

## Primera corrida

```bash
./meiga-school doctor
./meiga-school run wcd-30s --smoke 60
```

La salida debe contener:

- salida MEIGA comprimida;
- una única visualización `visualization.wrl`;
- tablas y resumen del análisis;
- 23 figuras PNG de 300 dpi;
- las mismas 23 figuras como PDF vectorial.

## Corridas largas

La campaña de 30 segundos usa 34 258 partículas. La campaña opcional de cinco
minutos usa 196 768 partículas y puede tardar decenas de minutos. Para esta
última se recomiendan 16 GiB de RAM y al menos seis núcleos disponibles.
