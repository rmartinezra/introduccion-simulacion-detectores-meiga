# Diseño del curso

## Audiencia inicial

Estudiantes de física, ingeniería o áreas afines con conocimientos básicos de terminal, Python y física de partículas. No se asumirá experiencia previa con Geant4 o Docker.

## Estrategia pedagógica

Cada módulo seguirá el mismo ciclo:

1. pregunta física;
2. modelo y supuestos;
3. configuración explícita;
4. predicción previa;
5. simulación reproducible;
6. análisis cuantitativo;
7. interpretación y limitaciones;
8. ejercicio de extensión.

## Separación de responsabilidades

- El contenedor proporciona compiladores, Geant4, MEIGA y datos necesarios.
- El repositorio proporciona configuraciones, actividades, análisis y pruebas.
- `/workspace` conserva entradas y resultados del estudiante.
- ARTI solo puede suministrar archivos de entrada compatibles; no forma parte del mantenimiento del curso.

## Criterio de terminado para una actividad

Una actividad estará lista cuando tenga objetivos, prerrequisitos, archivos de entrada, comandos verificados, resultado esperado, preguntas de análisis, tiempo aproximado y una prueba automática mínima.
