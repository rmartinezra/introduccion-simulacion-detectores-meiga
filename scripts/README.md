# Scripts

La interfaz recomendada es `./meiga-school`; evita que el estudiante tenga que
recordar rutas o nombres de scripts.

- `check-requirements.sh`: verifica WSL/Linux, Docker, contenedor, Python y recursos.
- `setup-python.sh`: crea `.venv` e instala las versiones del análisis.
- `run-wcd-campaign.sh`: ejecutor genérico para cualquier `campaign.json`.
- `ejecutar-wcd-30s.sh`: alias compatible para material anterior.

Todas las corridas quedan en `results/runs/<run-id>/`, nunca sobrescriben una
corrida previa y generan exactamente un `visualization.wrl`.
