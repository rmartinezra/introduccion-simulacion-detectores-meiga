# Contenedor

`Dockerfile` crea la capa docente `meiga_school:3.2-g4gro` sobre la imagen
robusta `meiga_school:3.0`. Incluye las dos campañas WCD autocontenidas, deja
el flujo de 5 min en `/opt/meiga-school/data/bariloche_5min.shw` y construye
G4GRO de forma aislada a partir del paquete original versionado.

Desde la raíz del repositorio:

```bash
docker build -f container/Dockerfile -t meiga_school:3.2-g4gro .
docker run -d --name meiga_school meiga_school:3.2-g4gro sleep infinity
```

La compilación de las tres aplicaciones principales sigue perteneciendo a la
imagen base. G4GRO usa una copia privada del árbol MEIGA, sus materiales y su
lista física; no modifica Hodoscopio, Torre ni WCD. El instalador también
verifica los SHA-256 del flujo largo y del archivo original de G4GRO.

Para ejecutar una prueba de tres neutrones:

```bash
docker exec meiga_school \
  /opt/meiga-school/external/G4GROSimulator/run-g4gro.sh smoke my-test
```

Las instrucciones para editar `.cc`, recompilar y validar G4GRO están en la
[documentación de la aplicación externa](../external-apps/g4gro/README.md).
