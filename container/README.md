# Contenedor

`Dockerfile` crea la capa docente `meiga_school:3.1` sobre la imagen robusta
`meiga_school:3.0`. Incluye las dos campañas WCD autocontenidas y deja el flujo
de 5 min en `/opt/meiga-school/data/bariloche_5min.shw`.

Desde la raíz del repositorio:

```bash
docker build -f container/Dockerfile -t meiga_school:3.1 .
docker run -d --name meiga_school meiga_school:3.1 sleep infinity
```

La compilación de MEIGA sigue perteneciendo a la imagen base; esta capa solo
añade materiales versionados del curso y verifica el SHA-256 del flujo largo.
