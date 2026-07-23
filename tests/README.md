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

`test_installation.py` comprueba el inicio rápido, la sintaxis Bash, la
construcción autónoma del contenedor, la integridad de la instantánea MEIGA, el
uso automático de `.venv` y que el instalador no elimine recursos Docker.
