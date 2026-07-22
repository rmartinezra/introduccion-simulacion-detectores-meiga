# Introducción a la simulación de detectores con MEIGA

Curso práctico para aprender a configurar, ejecutar, interpretar y extender simulaciones de detectores de radiación cósmica con MEIGA y Geant4.

## Estado

Repositorio en diseño inicial. La primera etapa convierte el entorno MEIGA existente en una plataforma reproducible, segura e intuitiva antes de publicar las actividades del curso.

## Alcance

El curso se concentra en tres aplicaciones:

- `G4HodoscopeSimulator`: telescopio de muones con hodoscopios.
- `G4TowSimulator`: aplicación de torre con planos de detección.
- `G4WCDSimulator`: detector Cherenkov de agua.

ARTI no se desarrollará ni modificará aquí. El material histórico de ARTI permanece disponible en el [repositorio del taller anterior](https://github.com/rmartinezra/workshopARTI_MEIGA).

## Objetivos de aprendizaje

Al finalizar, el estudiante podrá:

1. explicar el flujo físico y computacional de una simulación MEIGA;
2. ejecutar MEIGA de forma reproducible con Docker y WSL/Linux;
3. modificar archivos JSON y XML con unidades y parámetros válidos;
4. comparar los modos `UseEcoMug` y `UseARTI` sin modificar ARTI;
5. simular Hodoscopio, Torre y WCD;
6. analizar resultados y comunicar sus limitaciones estadísticas;
7. modificar una aplicación, recompilarla con `make` y validar el resultado.

## Recorrido propuesto

| Módulo | Tema | Producto del estudiante |
|---|---|---|
| 00 | Preparación del entorno | Diagnóstico reproducible del sistema |
| 01 | Fundamentos de MEIGA y Geant4 | Primera simulación de un muón |
| 02 | Configuración y geometría | Configuración validada y documentada |
| 03 | Hodoscopio | Estudio de aceptación y coincidencias |
| 04 | Torre | Comparación de geometrías y materiales |
| 05 | WCD | Respuesta en energía y carga |
| 06 | Análisis reproducible | Informe generado por scripts versionados |
| 07 | Proyecto final | Experimento completo y defendible |

## Organización

```text
analysis/       Herramientas unificadas de análisis
container/      Construcción y pruebas de la imagen MEIGA
docs/           Diseño, conceptos y referencias
modules/        Material pedagógico y actividades
scripts/        Instalación, diagnóstico y ejecución segura
tests/          Pruebas de configuración, análisis y contenedor
```

## Principios del proyecto

- Ningún script de instalación debe borrar imágenes o contenedores del estudiante.
- Todos los valores predeterminados relevantes deben estar explícitos.
- Cada ejemplo debe declarar entradas, salidas y tiempo esperado.
- Cada comando del curso debe verificarse automáticamente.
- Los análisis deben separar unidades físicas, selección de datos y visualización.
- La imagen del curso debe construirse desde archivos versionados, no desde un contenedor modificado manualmente.

Consulte [ROADMAP.md](ROADMAP.md) para las tareas y prioridades iniciales.
