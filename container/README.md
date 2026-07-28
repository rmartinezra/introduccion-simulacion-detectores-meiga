# Contenedor autónomo

`Dockerfile` construye
`rmartinezmaple/meiga-school:3.4.1-g4gro-viewer` sin depender de una imagen MEIGA local.
Parte de `ubuntu:22.04` e instala:

- Geant4 10.7.4 y sus conjuntos de datos;
- Boost y las bibliotecas de compilación;
- Hodoscopio, Torre y WCD;
- las campañas WCD de 30 segundos y 5 minutos;
- G4GRO en un árbol privado;
- `view3dscene`, Xvfb y noVNC para visualizar los WRL desde el navegador;
- `nano`, `vim`, `vi` y `less` para trabajar dentro del contenedor;
- fuentes, CMake, `make` y `g++` para recompilar.

## Construcción

Desde la raíz:

```bash
docker build \
  --file container/Dockerfile \
  --tag rmartinezmaple/meiga-school:3.4.1-g4gro-viewer \
  --tag meiga_school:3.4.1-g4gro-viewer \
  --build-arg BUILD_JOBS=2 \
  .
```

La primera construcción compila Geant4. Use uno o dos trabajos en equipos con
8 GiB de RAM y hasta ocho en equipos con suficientes núcleos y memoria.

El instalador recomendado ejecuta este proceso y crea el contenedor:

```bash
./meiga-school install
```

## Arranque

La imagen declara `CMD ["sleep", "infinity"]`; por ello no necesita un
`ENTRYPOINT` especial:

```bash
docker create \
  --name meiga_school \
  --init \
  --publish 127.0.0.1:6080:6080 \
  rmartinezmaple/meiga-school:3.4.1-g4gro-viewer
docker start meiga_school
```

## Verificaciones de integridad

La construcción falla si no coinciden:

- el SHA-256 del código fuente Geant4 10.7.4;
- el SHA-256 de `meiga-school-source.tar.gz`;
- los SHA-256 de los paquetes legado y actualizado de G4GRO;
- el SHA-256 del flujo WCD de 5 minutos.

La procedencia de la instantánea MEIGA está descrita en
[SOURCE.md](SOURCE.md).

## Pruebas rápidas

WCD y análisis desde el anfitrión:

```bash
./meiga-school run wcd-30s --smoke 60
```

Visor 3D de la última corrida:

```bash
latest_run="$(ls -dt results/runs/* | head -1)"
./meiga-school view "$latest_run/run/visualization.wrl"
```

Terminal interactiva con los editores incluidos:

```bash
./meiga-school shell
```

Después de entrar con el comando anterior, ejecute G4GRO dentro del contenedor:

```bash
./external/G4GROSimulator/run-g4gro.sh smoke my-test
```

Las instrucciones para modificar y recompilar G4GRO están en su
[README](../external-apps/g4gro/README.md).
