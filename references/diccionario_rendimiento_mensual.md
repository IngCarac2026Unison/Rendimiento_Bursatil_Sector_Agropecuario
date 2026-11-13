# Diccionario de datos: rendimiento mensual de acciones

**Archivo:** `data/interim/rendimiento_mensual.parquet`  
**Fuente:** Yahoo Finance, vía `yfinance` (precios diarios en `data/raw/RendimientoYahoo/`)  
**Periodo disponible:** enero de 2000 a septiembre de 2026 (321 meses); el análisis del proyecto usa 2013–2025.  
**Unidad de observación:** un mes, con una columna por ticker (formato ancho).

| Columna | Tipo | Descripción |
|---|---|---|
| `mes` (índice) | fecha | Último día calendario del mes (por ejemplo, `2013-01-31`), sin zona horaria. Único y en orden creciente. |
| `GRUMAB.MX` | decimal | Rendimiento mensual de la acción Serie B de Gruma. Fracción, no porcentaje: 0.05 equivale a +5 %. |
| `MINSAB.MX` | decimal | Rendimiento mensual de la acción Serie B de Minsa, con la misma definición. |

## Construcción

Se toma el último cierre ajustado por dividendos y splits de cada mes (`resample("ME")`, `last`) y se calcula `(cierre_t / cierre_{t-1}) - 1` por ticker.

## Rangos y faltantes

| Ticker | Mínimo | Mediana | Máximo | Faltantes | Meses con rendimiento 0 |
|---|---|---|---|---|---|
| `GRUMAB.MX` | -0.621 | 0.007 | 0.726 | 1 | 26 |
| `MINSAB.MX` | -0.565 | 0.000 | 0.467 | 1 | 215 |

- El único faltante es el primer mes (`2000-01-31`), que no tiene mes previo contra el cual calcular el rendimiento.
- Un rendimiento de 0 en Minsa suele indicar que la acción no cambió de precio en el mes por falta de operación, no una variación real. En 2013–2025 son 86 de 156 meses para Minsa y ninguno para Gruma; los 26 de Gruma son de 2000–2007, cuando casi no cotizaba.
- Por eso Minsa se usa solo como comparación secundaria.

## Reglas de calidad

Se validan con pandera (`rendimiento_bachoco/quality/yahoo.py`): una columna por ticker configurado y sin columnas extra, rendimientos mayores que -1 (se permiten faltantes), índice de fechas único y creciente, y ninguna columna completamente vacía.
