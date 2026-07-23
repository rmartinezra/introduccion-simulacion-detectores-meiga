# Procedencia de la instantánea MEIGA

`meiga-school-source.tar.gz` contiene la fuente docente usada para construir
Hodoscopio, Torre y WCD. Se versiona para que una máquina nueva pueda construir
la imagen sin acceder al servidor histórico ni depender de un contenedor
modificado manualmente.

## Origen

- repositorio histórico:
  `https://gitmilab.redclara.net/lidera/muografia/sim_detector.git`;
- commit base registrado: `0d98e6f970c044d15b16b4a120928c1abd491f8c`;
- instantánea tomada de la fuente validada de `meiga_school:3.0`;
- contiene los ajustes docentes de configuración, autocontención y
  recompilación desarrollados para este curso.

El archivo excluye `.git`, el directorio de compilación `cmake`, cachés de
Python, archivos WRL, logs y resultados.

## Integridad

```text
Archivo: container/meiga-school-source.tar.gz
SHA-256: bb36423c377e2fffe604c693df4ce8849d0455ec498691f39ed1c1342d7367b2
```

`install-meiga-school.sh` verifica este valor antes de extraer o compilar la
fuente.
