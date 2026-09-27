from pathlib import Path

import pandas as pd
from lxml import html

# La clave identifica el archivo descargado y cada valor indica dónde está el mercado.
# "Origen" se leerá después de la tabla y describe la procedencia del maíz,
# que puede ser distinta del estado donde se vende.
mercados = {
    "hermosillo": ("Sonora", "Hermosillo"),
    "culiacan": ("Sinaloa", "Culiacán"),
    "guadalajara": ("Jalisco", "Guadalajara"),
    "iztapalapa": ("Ciudad de México", "Iztapalapa"),
    "guadalupe": ("Nuevo León", "Guadalupe"),
}

# Acumulamos una observación por mes, mercado y origen antes de crear el CSV.
observaciones = []

for clave, (estado, mercado) in mercados.items():
    # Cada archivo de data/raw conserva la respuesta HTML original del SNIIM.
    # latin-1 permite leer los acentos usados por esta página antigua.
    ruta = Path(f"data/raw/sniim_{clave}_maiz_blanco.html")
    pagina = html.fromstring(ruta.read_text(encoding="latin-1"))

    # La segunda tabla contiene los precios; la primera es el encabezado del sitio.
    tabla = pagina.xpath("//table")[1]

    for renglon in tabla.xpath(".//tr"):
        # Extraemos el texto de cada celda y quitamos espacios sobrantes.
        celdas = [celda.text_content().strip() for celda in renglon.xpath("./td")]

        # Las filas de datos tienen 18 columnas y un año numérico en la sexta.
        # Así dejamos fuera títulos, encabezados y pies de página.
        if len(celdas) != 18 or not celdas[5].isdigit():
            continue

        # Nuestro análisis solo usa los años acordados para el proyecto.
        anio = int(celdas[5])
        if not 2013 <= anio <= 2025:
            continue

        # Las columnas 7 a 18 son enero a diciembre. start=1 asigna el número
        # correcto a cada mes; el día 01 representa el mes, no un precio diario.
        for mes, precio in enumerate(celdas[6:18], start=1):
            # Una celda vacía queda como faltante; no la convertimos en cero.
            observaciones.append({
                "fecha": f"{anio}-{mes:02d}-01",
                "estado_mercado": estado,
                "mercado": mercado,
                "origen": celdas[4],
                "producto": "Maíz blanco",
                "precio_mxn_kg": precio or None,
            })

# Pasamos la lista de observaciones a una tabla. to_numeric convierte los
# precios a números; errors="coerce" transforma celdas vacías o texto no
# numérico en un NaN.
datos = pd.DataFrame(observaciones)
datos["precio_mxn_kg"] = pd.to_numeric(datos["precio_mxn_kg"], errors="coerce")

# Comprobamos que todas las fechas sean válidas y estén en el periodo elegido.
fechas = pd.to_datetime(datos["fecha"], format="%Y-%m-%d", errors="raise")

if not fechas.dt.year.between(2013, 2025).all():
    raise ValueError("Hay fechas fuera del periodo 2013–2025.")

# En un mismo mes puede haber distintos orígenes, pero la combinación completa
# de fecha, mercado y origen debe aparecer una sola vez.
if datos.duplicated(["fecha", "mercado", "origen"]).any():
    raise ValueError("Hay filas repetidas para fecha, mercado y origen.")

# Revisamos solo los precios presentes: un faltante es válido, cero o menos no.
if (datos["precio_mxn_kg"].dropna() <= 0).any():
    raise ValueError("Hay precios iguales a cero o negativos.")

# Guardamos el conjunto limpio, mientras que index=False evita una columna artificial de filas.
salida = Path("data/processed/sniim_maiz_blanco_mensual.csv")
salida.parent.mkdir(parents=True, exist_ok=True)
datos.to_csv(salida, index=False)

# Mostramos un resumen para detectar cambios de cobertura en futuras descargas.
print(datos.groupby("mercado").size())
print(f"Total: {len(datos)}; precios faltantes: {datos['precio_mxn_kg'].isna().sum()}")
print(f"Guardado en {salida}")
