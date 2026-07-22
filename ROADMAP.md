# Hoja de ruta

## P0 — Base reproducible

### Contenedor MEIGA

- [ ] Sustituir el flujo manual `docker export/import` por un Dockerfile multi-etapa reproducible.
- [ ] Documentar la procedencia y versión exacta del código MEIGA y Geant4.
- [ ] Conservar únicamente Hodoscopio, Torre y WCD.
- [ ] Ejecutar como usuario sin privilegios dentro del contenedor.
- [ ] Incorporar `healthcheck`, etiquetas OCI y versión semántica.
- [ ] Añadir pruebas de compilación (`make`) y simulaciones mínimas.
- [ ] Producir imágenes `runtime` y `development` si la diferencia de tamaño lo justifica.
- [ ] Definir cómo se publicará la imagen y cómo se verificará su integridad.

### Configuración

- [ ] Crear esquemas formales para los JSON de simulación.
- [ ] Validar unidades, rangos, archivos y combinaciones incompatibles antes de iniciar Geant4.
- [ ] Mantener `DetectorProperties.xml` específico para cada aplicación.
- [ ] Mantener `DetectorList.xml` con parámetros explícitos y relevantes.
- [ ] Añadir ejemplos mínimos para `UseEcoMug` y `UseARTI`.
- [ ] Generar mensajes de error orientados a estudiantes.

### Instalación segura

- [ ] Separar diagnóstico, instalación y desinstalación.
- [ ] Detectar WSL2, Ubuntu nativo y Docker existente antes de actuar.
- [ ] Prohibir eliminaciones automáticas de `/var/lib/docker` y `/var/lib/containerd`.
- [ ] Crear `scripts/check-environment.sh` sin cambios en el sistema.
- [ ] Crear un instalador idempotente con confirmación para cambios privilegiados.
- [ ] Documentar recuperación y solución de problemas.

## P1 — Análisis científico

- [ ] Unificar `EAS3d.py`, `EASsec.py`, `EAStime.py` y `EASall.py` como paquete reutilizable.
- [ ] Crear una única interfaz: `meiga-analysis`.
- [ ] Validar columnas, unidades y metadatos de entrada.
- [ ] Separar lectura, filtros, estadísticas y figuras.
- [ ] Añadir análisis de energía depositada, carga, tiempo, eficiencia y aceptación.
- [ ] Añadir comparación entre configuraciones y propagación básica de incertidumbre.
- [ ] Exportar tablas CSV y figuras con metadatos reproducibles.
- [ ] Incorporar datos pequeños para pruebas y datos completos como descarga externa.
- [ ] Añadir pruebas unitarias y pruebas de regresión de las figuras esenciales.

## P1 — Experiencia del estudiante

- [ ] Crear comandos cortos mediante `Makefile` o `justfile`.
- [ ] Proporcionar una actividad guiada y una actividad abierta por módulo.
- [ ] Mostrar resultados esperados y errores frecuentes.
- [ ] Indicar tiempo de CPU, memoria y espacio requerido.
- [ ] Añadir rúbricas para informes y proyecto final.
- [ ] Crear glosario de física, Geant4 y MEIGA.

## P2 — Calidad y publicación

- [ ] Configurar integración continua para Markdown, Python, shell y configuraciones.
- [ ] Ejecutar pruebas de humo del contenedor en cada release.
- [ ] Definir licencia del material del curso y revisar licencias de MEIGA/Geant4.
- [ ] Publicar documentación navegable y releases numeradas.
- [ ] Añadir guía de contribución y política de citación.

## Fuera de alcance

- Modificar, modernizar o redistribuir ARTI.
- Mantener CORSIKA o sus modelos hadrónicos.
- Incorporar todas las aplicaciones de MEIGA en la primera edición.
