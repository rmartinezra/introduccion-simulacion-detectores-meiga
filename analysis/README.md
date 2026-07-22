# Análisis

La tubería reproducible unificada está implementada en
`wcd/analyze_wcd.py`. El mismo programa prepara escenarios, valida
las salidas MEIGA y genera:

- figuras con estética de artículo, etiquetas en inglés y archivos PNG a 300 dpi y PDF vectorial;
- vistas combinadas y paneles separados para cada observable dependiente del componente;
- histogramas de carga total, por componente de cascada y por especie;
- eficiencia y tasa frente al umbral de disparo, con intervalos de Wilson;
- distribuciones temporales, ancho de pulso y fracción de señal tardía;
- correlación entre momento, energía depositada y número de fotoelectrones;
- respuesta agregada por cascada primaria;
- tablas por evento, resumen JSON, informe Markdown y manifiesto con hashes.
- una escena `visualization.wrl` por corrida, registrada también en el manifiesto.

La carga principal se integra en una ventana explícita de 500 ns. La carga
bruta y los fotoelectrones fuera de la ventana se conservan por separado. La
salida de MEIGA representa número de fotoelectrones; todavía no es carga en pC,
cuentas ADC ni una calibración VEM.

## Uso directo

La forma recomendada es ejecutar desde WSL, en la raíz del repositorio:

```bash
./scripts/ejecutar-wcd-30s.sh
```

Para analizar nuevamente una salida ya generada, consulte la ayuda:

```bash
python3 analysis/wcd/analyze_wcd.py --help
python3 analysis/wcd/analyze_wcd.py analyze --help
python3 analysis/wcd/analyze_wcd.py replot --help
```

Las versiones exactas usadas en una corrida quedan registradas en su
`manifest.json`. `requirements.txt` documenta el entorno Python de referencia.
