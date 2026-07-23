# Scripts

La interfaz pública es `./meiga-school`; los usuarios no necesitan invocar los
scripts internos.

- `install.sh`: valida Linux/WSL y Docker, instala `.venv`, construye o descarga
  la imagen y crea/inicia el contenedor sin borrar recursos existentes.
- `check-requirements.sh`: diagnostica plataforma, Python, Docker, imagen,
  contenedor, memoria, CPU y disco.
- `setup-python.sh`: crea `.venv` con las versiones científicas fijadas.
- `run-wcd-campaign.sh`: prepara, simula y analiza cualquier `campaign.json`.
- `ejecutar-wcd-30s.sh`: alias compatible con material anterior.

Inicio normal:

```bash
./meiga-school install
./meiga-school run wcd-30s --smoke 60
```

Cada corrida queda en `results/runs/<run-id>/`, nunca sobrescribe otra corrida
y genera exactamente un `visualization.wrl`.
