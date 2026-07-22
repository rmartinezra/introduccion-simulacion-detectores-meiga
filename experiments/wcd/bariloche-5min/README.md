# WCD campaign: five-minute Bariloche flux

Esta campaña autocontenida reproduce el tanque original (`R=1.05 m`,
`H=0.90 m`, Tyvek) con 196 768 secundarios ARTI y 300 s de exposición.

El archivo `input/bariloche_5min.shw` se conserva dentro del repositorio y se
instala también en la imagen del curso. Su SHA-256 es
`db4f9e09a2b43898faffc7fea3446cba072777ff3cf9bb6ebe79296da56ced66`.

Prueba rápida:

```bash
./meiga-school run wcd-5min --smoke 60
```

Corrida completa y análisis:

```bash
./meiga-school run wcd-5min
```

La corrida completa puede tardar decenas de minutos. Genera exactamente un
`visualization.wrl`, tablas normalizadas y las mismas 23 figuras científicas
de la campaña de 30 s, tanto en PNG como en PDF.
