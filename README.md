# Introducción a la simulación de detectores con MEIGA

Ejecute una simulación de un detector Cherenkov de agua (WCD) y genere
automáticamente el análisis físico, las tablas y las gráficas. No necesita
instalar Geant4 ni MEIGA directamente en su sistema: ambos se construyen dentro
de Docker.

## Primera simulación WCD

### 1. Requisitos

- Linux de 64 bits o Windows con WSL2.
- Docker Engine en Linux o Docker Desktop con integración WSL2.
- Git, Bash y Python 3.10 o posterior.
- 8 GiB de RAM y 15 GiB libres como mínimo.

La guía [Instalación en WSL y Linux](docs/installation.md) contiene comandos
para Ubuntu, Debian, Fedora, Arch Linux y openSUSE.

### 2. Descargar e instalar

Abra una terminal Linux o WSL:

```bash
git clone https://github.com/rmartinezra/introduccion-simulacion-detectores-meiga.git
cd introduccion-simulacion-detectores-meiga
./meiga-school install
```

El instalador crea `.venv`, instala NumPy y Matplotlib, descarga la imagen
precompilada `rmartinezmaple/meiga-school:3.2-g4gro` desde Docker Hub y deja
iniciado el contenedor `meiga_school`. Si la descarga no está disponible,
construye Geant4 10.7.4 y MEIGA desde los archivos versionados.

No es necesario activar manualmente `.venv`.

Para exigir la descarga desde Docker Hub sin intentar una compilación local:

```bash
./meiga-school install --pull
```

### 3. Ejecutar WCD y el análisis

La prueba recomendada usa 60 partículas:

```bash
./meiga-school run wcd-30s --smoke 60
```

Este único comando:

1. prepara una muestra reproducible del flujo;
2. ejecuta `G4WCDSimulator`;
3. guarda exactamente una visualización `visualization.wrl`;
4. analiza carga, energía, tiempos, eficiencia y componentes;
5. genera 23 figuras PNG de 300 dpi y 23 PDF vectoriales.

Cada ejecución crea un identificador nuevo y nunca sobrescribe resultados.
Al terminar, muestra la ruta exacta, normalmente:

```text
results/runs/<run-id>/
├── run/          configuraciones, salida MEIGA y visualization.wrl
├── analysis/     tablas, métricas e informe reproducible
└── plots/        figuras PNG y PDF
```

### 4. Verificar la instalación

```bash
./meiga-school doctor
```

El diagnóstico identifica la distribución, Python, Docker, la imagen, el
contenedor y los recursos disponibles.

## Descarga manual con Docker

Si solo desea preparar el contenedor manualmente:

```bash
docker pull rmartinezmaple/meiga-school:3.2-g4gro
docker run -d \
  --name meiga_school \
  rmartinezmaple/meiga-school:3.2-g4gro
```

Compruebe que está activo y que contiene el WCD:

```bash
docker ps --filter name=meiga_school
docker exec meiga_school \
  test -x /opt/meiga-school/G4WCDSimulator/G4WCDSimulator
```

La imagen también está publicada como
[`rmartinezmaple/meiga-school:latest`](https://hub.docker.com/r/rmartinezmaple/meiga-school).
Para producir resultados y gráficas se recomienda conservar este repositorio:
`./meiga-school` coordina el contenedor y el análisis Python.

## Comandos frecuentes

```bash
# Ayuda
./meiga-school help

# Prueba corta y rápida
./meiga-school run wcd-30s --smoke 60

# Prueba separando las componentes EM, muónica y hadrónica
./meiga-school run wcd-30s --smoke 300 --components

# Flujo completo de 30 segundos
./meiga-school run wcd-30s --components

# Proyecto largo con flujo de 5 minutos
./meiga-school run wcd-5min --components
```

Para repetir exactamente una configuración, declare semilla e identificador:

```bash
./meiga-school run wcd-30s \
  --smoke 60 \
  --seed 2026072230 \
  --run-id mi-validacion
```

## Compatibilidad

Los scripts se ejecutan en Bash y no dependen de `apt`, `systemd` ni rutas de
WSL. El mismo flujo funciona con Docker en:

- WSL2 con Ubuntu o Debian;
- Ubuntu y Debian nativos;
- Fedora, RHEL y distribuciones derivadas;
- Arch Linux y openSUSE;
- otras distribuciones Linux con Bash, Docker y Python 3.10+.

El contenedor está construido desde Ubuntu 22.04, por lo que la versión de las
bibliotecas científicas de la distribución anfitriona no cambia la física de
la simulación. Consulte [installation.md](docs/installation.md) para
diagnóstico y alternativas de instalación.

## Campañas WCD

- [Flujo de 30 segundos](experiments/wcd/flux-30s/README.md): campaña principal
  para prácticas y análisis por componentes.
- [Flujo de 5 minutos](experiments/wcd/bariloche-5min/README.md): proyecto largo
  con 196 768 partículas.

El analizador [analyze_wcd.py](analysis/wcd/analyze_wcd.py) es único para ambas
campañas. Usa etiquetas en inglés y produce vistas combinadas y por panel para
las componentes electromagnética, muónica y hadrónica.

## Alcance del curso

El curso se concentra en:

- `G4HodoscopeSimulator`: telescopio de muones con hodoscopios;
- `G4TowSimulator`: torre con planos de detección;
- `G4WCDSimulator`: detector Cherenkov de agua.

ARTI no se modifica. El material histórico permanece en el
[taller anterior](https://github.com/rmartinezra/workshopARTI_MEIGA).

Los módulos llevan al estudiante desde la primera corrida hasta un proyecto
completo:

| Módulo | Tema | Producto |
|---|---|---|
| 00 | Preparación | Entorno diagnosticado |
| 01 | Fundamentos MEIGA/Geant4 | Primera simulación |
| 02 | Configuración y geometría | JSON/XML validados |
| 03 | Hodoscopio | Aceptación y coincidencias |
| 04 | Torre | Comparación de geometrías |
| 05 | WCD | Respuesta en energía y carga |
| 06 | Análisis | Informe reproducible |
| 07 | Proyecto final | Experimento defendible |

## Aplicación externa G4GRO

La imagen incluye G4GRO como aplicación opcional de un colaborador. Su paquete
original permanece intacto y se compila contra una copia privada de MEIGA para
que sus materiales y lista física no afecten Hodoscopio, Torre ni WCD. Consulte
la [guía de G4GRO](external-apps/g4gro/README.md) para ejecutarla, editar `.cc`
y recompilar.

## Organización

```text
analysis/       análisis unificado del WCD
container/      construcción autónoma de Geant4 y MEIGA
docs/           instalación, conceptos y requisitos
experiments/    campañas autocontenidas con JSON, XML y flujos
external-apps/  aplicaciones externas aisladas
modules/        material pedagógico
results/        salidas locales, excluidas de Git
scripts/        instalación, diagnóstico y ejecución
tests/          pruebas automáticas
```

## Principios del proyecto

- Ningún instalador elimina imágenes, contenedores o resultados existentes.
- Todos los valores predeterminados relevantes son explícitos.
- Cada corrida declara entrada, semilla y ubicación de salida.
- Los análisis separan unidades físicas, selección de datos y visualización.
- La imagen se construye desde archivos versionados, no desde un contenedor
  modificado manualmente.

Consulte [ROADMAP.md](ROADMAP.md) para el desarrollo del curso.
