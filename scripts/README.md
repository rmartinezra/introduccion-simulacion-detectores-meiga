# Scripts

Los scripts de este directorio deberán ser seguros e idempotentes.

Separación prevista:

- `check-environment.sh`: diagnóstico de WSL/Linux, Docker, recursos y permisos;
- `install-docker.sh`: instalación opcional y no destructiva;
- `start-course.sh`: creación o arranque del contenedor del curso;
- `smoke-test.sh`: comprobación de las tres aplicaciones;
- `clean-results.sh`: limpieza limitada a resultados generados por el curso.

La desinstalación deberá ser un proceso separado, explícito y documentado.
