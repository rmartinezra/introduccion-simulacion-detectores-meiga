# Requisitos para estudiantes

## Plataforma mínima

- Windows 10/11 de 64 bits con WSL2, o Linux de 64 bits.
- Ubuntu 22.04 o 24.04 dentro de WSL2.
- Docker Desktop con integración para la distribución Ubuntu, o Docker Engine
  nativo en Linux.
- 4 núcleos de CPU, 8 GiB de RAM y 15 GiB libres en disco.

## Configuración recomendada

- 8 núcleos de CPU, 16 GiB de RAM y 30 GiB libres.
- Guardar el repositorio dentro del sistema de archivos de WSL (`~/...`) para
  obtener mejor rendimiento que bajo `/mnt/c/...`.
- Ubuntu 24.04 y Docker Desktop actualizados.

No se requiere GPU ni tarjeta NVIDIA.

## Programas

Dentro de Ubuntu/WSL:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv
```

La imagen/contenedor `meiga_school` debe estar instalada por el docente. Las
dependencias del análisis (`numpy==1.26.4` y `matplotlib==3.6.3`) se instalan
con:

```bash
./meiga-school setup
```

## Verificación y primera corrida

```bash
./meiga-school doctor
./meiga-school run wcd-30s --smoke 60
```

La prueba corta debe crear una carpeta bajo `results/runs/` con:

- salida comprimida de MEIGA;
- un solo archivo `visualization.wrl`;
- tablas y resumen del análisis;
- 23 figuras PNG de 300 dpi y sus 23 versiones PDF vectoriales.

## Recursos para las corridas largas

La campaña de 30 s usa 34 258 partículas. La campaña opcional de 5 min usa
196 768 partículas y puede tardar decenas de minutos. Para esta última se
recomiendan 16 GiB de RAM y al menos 6 núcleos disponibles.
