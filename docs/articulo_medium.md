# Cómo extraer y limpiar los precios del maíz del SNIIM con Python

*Un tutorial para descargar, leer y limpiar una tabla gubernamental que nunca fue pensada para ser leída por un programa.*

*Por Manuel Gortarez, Marco Ramonet y Gamaliel Sandoval*

---

El SNIIM (Sistema Nacional de Información e Integración de Mercados) publica los precios de granos, frutas y hortalizas en las centrales de abasto de México. Es de las pocas fuentes públicas con precios mensuales por mercado desde 1998.

El problema es cómo los publica. No hay API ni botón de "descargar CSV". Los datos solo aparecen como una página web después de llenar un formulario, y la página abre con esta línea:

```html
<meta name="GENERATOR" content="Microsoft FrontPage Express 2.0">
```

En este tutorial vamos a sacar de ahí el precio mensual del maíz blanco y dejarlo en una tabla limpia. El método sirve igual para otros granos y otros mercados del mismo anuario.

## Lo que vamos a enfrentar

- **No hay URL directa.** La tabla se obtiene enviando un formulario con `POST`.
- **La codificación no es UTF-8.** Los acentos vienen en latin-1.
- **El HTML no tiene estructura.** No hay `<th>`, ni `id`, ni `class`.
- **La tabla está en formato ancho.** Una fila por año, con doce columnas de meses.
- **Las celdas vacías significan "no hubo precio"**, no cero.

Necesitas tres librerías:

```bash
pip install requests lxml pandas
```

## Paso 1: entender el formulario

El anuario de granos está en `anuariosgran1.asp`. En el navegador eliges un mercado y un producto, y oprimes "Aceptar". Si inspeccionas la petición (pestaña *Red* de las herramientas del navegador), verás que el formulario envía tres campos:

- `cent`: el código del mercado.
- `prod`: el código del producto. Maíz blanco es `OMABLAN`.
- `ACCION`: el texto del botón, `Aceptar`.

Para el ejemplo usaremos cinco mercados:

```text
Código  Mercado       Estado
260     Hermosillo    Sonora
250     Culiacán      Sinaloa
140     Guadalajara   Jalisco
100     Iztapalapa    Ciudad de México
191     Guadalupe     Nuevo León
```

## Paso 2: descargar la página

```python
from pathlib import Path

import requests

URL = "http://www.economia-sniim.gob.mx/SNIIM-AN/estadisticas/anuariosgran1.asp"


def descargar(codigo: str, mercado: str, destino: Path) -> None:
    if destino.exists():
        return

    respuesta = requests.post(
        URL,
        data={"cent": codigo, "prod": "OMABLAN", "ACCION": "Aceptar"},
        timeout=60,
    )
    respuesta.raise_for_status()

    if mercado not in respuesta.text:
        raise ValueError(f"El SNIIM no devolvió la tabla de {mercado}.")

    destino.write_bytes(respuesta.content)
```

Hay tres detalles en esta función:

**No descarga lo que ya existe.** Si el archivo está en disco, termina. Puedes correr el script muchas veces sin saturar un servidor que no está hecho para eso.

**No confía en el código 200.** Un sitio así puede responder "todo bien" y entregar una página sin datos. `raise_for_status()` no detecta eso, así que revisamos que la respuesta mencione el mercado que pedimos.

**Guarda bytes, no texto.** Con `respuesta.content` el archivo queda idéntico a lo que mandó el servidor. Si después lees mal un acento, el original sigue intacto y no hay que volver a descargar.

## Paso 3: leer el HTML

Cada página pesa cerca de 100 KB, y casi todo es formato. Cada celda viene envuelta así:

```html
<td bgcolor="#008000" align="center">
  <font face="Arial" color="#FFFFFF" size="2"><b> $Max</b></font>
</td>
```

El primer tropiezo es la codificación. Si abres el archivo como UTF-8, falla:

```text
'utf-8' codec can't decode byte 0xf3 in position 408
```

Ese byte es la "ó" de "Información" en latin-1. Hay que indicarlo de forma explícita:

```python
from lxml import html

pagina = html.fromstring(destino.read_text(encoding="latin-1"))
tabla = pagina.xpath("//table")[1]
```

El segundo tropiezo es ubicar la tabla. La página tiene tres `<table>` sin identificador. La primera es el encabezado del sitio; la segunda, la de precios. Por eso tomamos la posición `[1]`.

## Paso 4: separar los datos del adorno

Así se ven las primeras filas de la tabla de Hermosillo, ya como texto:

```text
['Precios en pesos por kg']
['Maíz blanco Sonora: Mercado de Abasto "Francisco I. Madero" de Hermosillo']
['Variables estadísticas', '', 'Promedios mensuales']
['$Max', '$Min', 'Varianza', 'DesEst', 'Origen', 'Año', 'Ene', 'Feb', ..., 'Dic']
['2.00', '1.80', '0.01', '0.07', 'Sonora', '1998', '1.90', '1.88', ..., '2.00']
['2.00', '2.00', '0', '0', 'Chihuahua', '1998', '', '', '', '', '2.00', '', ...]
```

Las tres primeras son títulos y la cuarta es el encabezado. Las filas de datos comparten dos rasgos: tienen exactamente 18 celdas y la sexta es un año. Con eso basta para filtrarlas:

```python
celdas = [celda.text_content().strip() for celda in renglon.xpath("./td")]

if len(celdas) != 18 or not celdas[5].isdigit():
    continue
```

La condición `isdigit()` es la que descarta el encabezado: también tiene 18 celdas, pero en la sexta dice "Año".

Filtrar por la forma del dato resiste mejor un cambio en la página que decir "los datos empiezan en la fila cinco".

## Paso 5: de ancho a largo

Una fila del SNIIM se ve así:

```text
Origen   Año   Ene   Feb   Mar   Abr   May   Jun   Jul   Ago   Sep   Oct   Nov   Dic
Sinaloa  2013  6.36  6.00  6.50  6.24  5.62  5.30  5.56  5.40  5.32  5.72  5.80  5.62
```

Es cómoda para leer, pero no para analizar. Lo que queremos es una fila por cada precio. Esta función junta los pasos 3, 4 y 5:

```python
def leer_tabla(ruta: Path, mercado: str, desde: int, hasta: int) -> list[dict]:
    pagina = html.fromstring(ruta.read_text(encoding="latin-1"))
    tabla = pagina.xpath("//table")[1]

    filas = []
    for renglon in tabla.xpath(".//tr"):
        celdas = [celda.text_content().strip() for celda in renglon.xpath("./td")]

        if len(celdas) != 18 or not celdas[5].isdigit():
            continue

        anio = int(celdas[5])
        if not desde <= anio <= hasta:
            continue

        for mes, precio in enumerate(celdas[6:18], start=1):
            filas.append({
                "fecha": f"{anio}-{mes:02d}-01",
                "mercado": mercado,
                "origen": celdas[4],
                "precio_mxn_kg": precio or None,
            })
    return filas
```

Vale la pena detenerse en tres puntos:

**La fecha usa el día 01 por convención.** El dato es un promedio mensual, no la cotización del primer día del mes.

**`precio or None` protege los faltantes.** Una celda vacía llega como cadena vacía. Si la convirtieras a cero, estarías diciendo que el maíz se regaló ese mes.

**El origen no es el mercado.** La columna "Origen" indica de dónde viene el maíz, no dónde se vende. En Hermosillo, casi la mitad de los precios corresponde a maíz traído de Sinaloa. Y un mismo mercado puede tener varios orígenes en el mismo mes:

```text
Culiacán      Sinaloa, Jalisco
Guadalajara   Jalisco, Importación
Guadalupe     Tamaulipas, Sinaloa, Tabasco, Coahuila
Hermosillo    Sinaloa, Sonora, Jalisco
Iztapalapa    Sinaloa, México
```

Por eso cada fila representa **un mes, un mercado y un origen**. Si asumes una sola fila por mes y mercado, mezclas o pierdes precios sin darte cuenta.

Las primeras cuatro columnas (`$Max`, `$Min`, `Varianza`, `DesEst`) las dejamos fuera. No coinciden con los promedios mensuales: en 2013 el máximo dice 6.80, pero el mes más alto es 6.50.

## Paso 6: limpiar y validar

Con las filas de todos los mercados en una lista, armamos la tabla y convertimos los tipos:

```python
import pandas as pd

datos = pd.DataFrame(filas)
datos["fecha"] = pd.to_datetime(datos["fecha"], format="%Y-%m-%d")
datos["precio_mxn_kg"] = pd.to_numeric(datos["precio_mxn_kg"], errors="coerce")
```

Antes de guardar, dos comprobaciones baratas:

```python
assert not datos.duplicated(["fecha", "mercado", "origen"]).any(), "Hay filas repetidas"
assert (datos["precio_mxn_kg"].dropna() > 0).all(), "Hay precios en cero o negativos"

datos.to_csv("maiz_blanco_mensual.csv", index=False)
```

La primera confirma que la combinación fecha, mercado y origen es única. La segunda revisa solo los precios presentes: un faltante es válido, un cero no.

Es mejor que el script se detenga a que entregue un archivo con datos malos en silencio.

## El resultado

Con los cinco mercados y los años 2013 a 2025, la tabla queda así:

```text
fecha       mercado     origen   precio_mxn_kg
2013-01-01  Hermosillo  Sinaloa  6.36
2013-02-01  Hermosillo  Sinaloa  6.00
2013-03-01  Hermosillo  Sinaloa  6.50
2013-04-01  Hermosillo  Sinaloa  6.24
```

Son 960 filas, de las cuales 791 tienen precio. Los valores van de 3.50 a 16.25 pesos por kilo.

Las otras 169 filas, casi el 18 %, están vacías. No es un error: son meses en los que el SNIIM no registró maíz de ese origen en ese mercado. Qué hacer con ellas (promediar orígenes, quedarte con el principal, interpolar) depende de tu análisis, y conviene decidirlo después, no durante la extracción.

## En resumen

- **Guarda la respuesta original** antes de transformarla.
- **Revisa el contenido**, no solo el código de estado.
- **Filtra por la forma del dato**, no por su posición.
- **Un faltante no es un cero.**
- **Entiende cada columna** antes de usarla: origen y mercado no son lo mismo.
- **Valida antes de guardar.**

Los sitios gubernamentales antiguos intimidan, pero casi siempre siguen un patrón fijo. Una vez que lo encuentras, bastan unas cuantas líneas de Python para convertirlos en datos que sí puedes analizar.
