# Pruebas

La estrategia de pruebas cubrirá:

- sintaxis y esquemas de JSON/XML;
- existencia de todas las rutas referenciadas;
- compilación independiente de cada aplicación;
- simulación mínima reproducible;
- lectura y análisis de resultados;
- seguridad básica de los scripts de instalación;
- documentación y comandos del curso.

La campaña WCD incluye `test_wcd_campaign.py`, que verifica el conteo y la
clasificación del flujo, el muestreo estratificado usado por `--smoke` y los
observables temporales básicos.
