# Diccionario de datos: precio mensual de la tortilla de maíz

**Archivo:** `data/processed/precio_tortilla_mensual.csv`  
**Fuente:** Procuraduría Federal del Consumidor (PROFECO), programa [Quién es Quién en los Precios](https://datos.profeco.gob.mx/index.php) (QQP)  
**Periodo con datos:** enero de 2015 a marzo de 2026, con huecos (ver cobertura)  
**Unidad de observación:** un mes, un giro de establecimiento y un nivel geográfico (nacional o estado).

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha` | fecha | Primer día del mes. |
| `nivel` | texto | `nacional` o `estado`. |
| `estado` | texto | Entidad federativa (32); vacío en `nacional`. |
| `giro` | texto | `tortilleria` o `autoservicio` (supermercados y tiendas de autoservicio). |
| `precio_mediana_mxn_kg` | decimal | Mediana del precio en pesos por kg, 2 decimales. |
| `precio_p25`, `precio_p75` | decimal | Percentiles 25 y 75 del precio. |
| `n_registros` | entero | Registros de precio (un establecimiento se observa varias veces al mes, una por quincena). |
| `n_establecimientos` | entero | Establecimientos distintos (cadena, nombre comercial y dirección). |

## Construcción

- Se toman los registros cuyo producto es tortilla de maíz y cuya presentación es `1 Kg. Granel`; el precio es por kg. En autoservicio la tortilla se vende con la misma presentación, por lo que es comparable por kg.
- **Estado:** mediana, p25 y p75 de los registros del estado, mes y giro.
- **Nacional:** mediana de las medianas estatales (cada estado pesa igual). Así se evita que las entidades con más establecimientos levantados, como la Ciudad de México, dominen el promedio. En `nacional`, `precio_p25` y `precio_p75` son los percentiles de las medianas estatales; `n_registros` y `n_establecimientos` cuentan todos los registros del país.
- Los registros sin fecha, precio o estado válido se descartan. Los nombres de estado se normalizan (sin acentos o con ellos en la fuente) a los 32 oficiales.
- Giros distintos de tortillería y autoservicio (mercados, panaderías, tiendas de conveniencia, central de abasto, etc.) no entran al archivo mensual, pero sí a la tabla intermedia.
- Otras presentaciones de tortilla de maíz (`1 Kg. Granel. Amarilla`, `Bolsa 1 Kg. Blanca`, `Bolsa 500 Gr.`, etc.; menos del 5 % de los registros) se conservan solo en la tabla intermedia.

## Tabla intermedia

`data/interim/PROFECO/qqp_tortilla_maiz.parquet`: un registro de precio por fila, con `fecha`, `estado`, `municipio`, `giro`, `cadena_comercial`, `nombre_comercial`, `direccion`, `presentacion` y `precio_mxn`.

## Cobertura real

Los archivos `QQP_AAAA.rar` que publica PROFECO son solo el primer volumen de un RAR multivolumen. Contienen las primeras quincenas de cada año y el último CSV está truncado; ese CSV se omite. El resto del año no se puede recuperar de la fuente. Los archivos de años distintos son diferentes (hash SHA-256 distinto); coinciden en tamaño porque ese es el tamaño del volumen.

| Año | Meses con datos | Registros tortillería (1 kg granel) | Mediana nacional de tortillería, ene (MXN/kg) | Promedio de medianas mensuales (MXN/kg) |
|---|---|---|---|---|
| 2015 | 1–8 | 30 949 | 12.25 | 13.41 |
| 2016 | 1–7 | 16 104 | 14.00 | 13.64 |
| 2017 | 1–8 | 20 200 | 14.50 | 14.76 |
| 2018 | 1–8 | 19 557 | 15.00 | 15.00 |
| 2019 | 1–9 | 18 413 | 16.00 | 15.33 |
| 2020 | 1–9 | 15 539 | 16.00 | 16.08 |
| 2021 | 1–10 | 18 033 | 16.25 | 17.91 |
| 2022 | 1–3 | 4 740 | 19.00 | 19.67 |
| 2023 | 1–7 | 12 579 | 22.00 | 23.29 |
| 2024 | 1–9 | 16 051 | 24.00 | 24.00 |
| 2025 | 1–7 | 16 422 | 24.00 | 24.46 |
| 2026 | 1–3 | 6 153 | 25.00 | 25.00 |

Autoservicio tiene los mismos meses por año, con 2 877 a 19 820 registros anuales (mediana nacional de enero: 9.90 en 2015 y 13.50 en 2026).

Los meses faltantes de cada año se reportan como advertencia en `validate_profeco`. El último mes de cada año disponible puede tener solo la primera quincena.

## Notas

- En 2015–2021 y 2023–2026 la fuente usa nombres de columnas y de giro consistentes; el giro viene como `tortillerias` y `supermercado / tienda de autoservicio`.
- El rango plausible para la validación es 5–60 MXN/kg.
- Metadatos del conjunto: <https://datos.profeco.gob.mx/docs/qqp/QQP_metadatos_dataset.csv>
