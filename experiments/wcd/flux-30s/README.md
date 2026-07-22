# Campaña WCD: flujo de 30 segundos

Esta carpeta define una campaña autocontenida para inyectar sobre el WCD el
archivo de secundarios ARTI de Bucaramanga integrado durante 30 segundos.

## Contenido

- `campaign.json`: duración, semilla, modo de simulación y opciones de salida.
- `DetectorList.xml`: geometría de inyección y posición del WCD.
- `DetectorProperties.xml`: dimensiones explícitas del tanque.
- `input/bga_30s.shw`: copia local del flujo de referencia.

El script `scripts/ejecutar-wcd-30s.sh` crea una carpeta independiente para
cada escenario. Cada una contiene su propio flujo, JSON, XML, log y salida; no
depende de rutas externas una vez preparada.

Cada corrida produce además `visualization.wrl` en su carpeta de salida. Es una
escena VRML2 única de la geometría WCD, creada desde el escenario `all`. Las
trayectorias permanecen desactivadas para evitar un archivo enorme con decenas
de miles de eventos. Incluso al usar `--components` se genera un solo `.wrl`.

## Ejecución

Desde WSL, en la raíz del curso:

```bash
./meiga-school run wcd-30s
```

Para ejecutar además inyecciones independientes de las componentes
electromagnética, muónica y hadrónica:

```bash
./meiga-school run wcd-30s --components
```

Prueba rápida, sin afirmar que representa 30 segundos completos:

```bash
./meiga-school run wcd-30s --smoke 60
```

## Interpretación física

En modo `eCircle`, MEIGA conserva especie y momento de ARTI, pero vuelve a
muestrear la posición de cada secundario uniformemente sobre el disco de
inyección. La duración de 30 s describe la biblioteca de flujo original; la
tasa detectada depende también del área de inyección y de la aceptancia del
tanque.

La carga almacenada por MEIGA es un número de fotoelectrones, no carga
eléctrica en pC ni cuentas ADC. La conversión a una traza electrónica requiere
ganancia, forma de pulso, ruido, digitalización y saturación.

El análisis instrumental usa de forma explícita una ventana de adquisición de
`500 ns` desde la inyección. También conserva la carga bruta de MEIGA y cuenta
los fotoelectrones posteriores a la ventana para estudiar señales retardadas.
