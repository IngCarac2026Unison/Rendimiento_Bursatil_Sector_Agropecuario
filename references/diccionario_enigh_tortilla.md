# Diccionario de datos: consumo y gasto de tortilla de maíz por hogar (ENIGH)

**Archivo:** `data/processed/enigh_tortilla_hogar.csv`  
**Fuente:** INEGI, [Encuesta Nacional de Ingresos y Gastos de los Hogares (ENIGH), Nueva Construcción](https://www.inegi.org.mx/programas/enigh/nc/)  
**Años:** 2014, 2016, 2018, 2020, 2022 y 2024 (encuesta bienal)  
**Unidad de observación:** un año y un nivel de desagregación (`nacional`, una entidad federativa o un decil de ingreso).

| Columna | Tipo | Descripción |
|---|---|---|
| `anio` | entero | Año de la encuesta. |
| `nivel` | texto | `nacional`, `entidad` o `decil`. |
| `clave_nivel` | texto | `nacional`; clave de entidad de 2 dígitos (`01`–`32`); o decil de ingreso `1`–`10` (1 = menor ingreso). |
| `kg_dia_hogar` | decimal | Kilogramos diarios de tortilla comprados por hogar, promedio ponderado sobre todos los hogares (incluye hogares sin compra). Solo compra monetaria (`G1`). |
| `kg_dia_hogar_compradores` | decimal | Igual, pero solo entre hogares que compraron en la semana de referencia. |
| `kg_dia_hogar_total` | decimal | Kilogramos diarios por hogar incluyendo compra (`G1`), autoconsumo (`G3`), regalo (`G5`) y transferencia (`G6`). |
| `gasto_dia_hogar_mxn` | decimal | Gasto diario en tortilla por hogar, pesos corrientes, solo `G1`, todos los hogares. |
| `precio_implicito_mxn_kg` | decimal | Gasto total entre kilogramos totales ponderados (`G1`), pesos corrientes por kg. |
| `precio_mediano_hogar_mxn_kg` | decimal | Mediana ponderada, entre hogares compradores, del gasto entre kilogramos de cada hogar. |
| `pct_hogares_compran` | decimal | Porcentaje ponderado de hogares con compra (`G1`) en la semana de referencia (0–100). |
| `kg_dia_per_capita` | decimal | Kilogramos diarios de compra por integrante (compra total ponderada entre personas ponderadas, `tot_integ`). |
| `n_hogares_muestra` | entero | Hogares de la muestra en el grupo. |
| `hogares_expandidos` | entero | Hogares representados (suma de factores de expansión). |

El intermedio por hogar está en `data/interim/ENIGH/tortilla_hogar_{anio}.parquet` (`folioviv`, `foliohog`, `entidad`, `factor`, `tot_integ`, `ing_cor`, `kg_sem_g1`, `gasto_sem_g1`, `kg_sem_total`).

## Metodología

- **Tablas:** `gastoshogar` (gasto y cantidad por clave y tipo de gasto) y `concentradohogar` (factor de expansión, integrantes e ingreso corriente trimestral `ing_cor`). El factor es `factor_hog` en 2014 y `factor` desde 2016.
- **Clave de tortilla de maíz:** `A004` en 2014–2022; `011131` en 2024. No se confunde con harina de maíz (`A002` / `011121`).
- **Periodo de referencia:** `cantidad` y `gasto` corresponden a 7 días (`gasto_tri` equivale a `gasto` × 90/7). El consumo diario es la cantidad semanal entre 7.
- **Tipo de gasto:** `G1` es compra monetaria y base de gasto y precio; `G3` autoconsumo, `G5` regalo, `G6` transferencia (solo en `kg_dia_hogar_total`).
- **Ponderación:** todos los promedios usan el factor de expansión sobre todos los hogares del grupo; los hogares sin registro de tortilla cuentan con cero.
- **Entidad:** primeros dos dígitos de `folioviv`.
- **Deciles:** de `ing_cor`, ponderados por el factor de expansión, sobre todos los hogares del año.

## Comparabilidad

- 2014 se publica con la serie anterior de tablas (un solo zip, `factor_hog`); 2016 en adelante usa la Nueva Serie. Los datos de 2014 son comparables en clave y unidad, pero conviene confirmar la continuidad del marco muestral antes de interpretar el cambio 2014–2016.
- En 2024 el catálogo de gasto cambió de claves alfanuméricas a claves numéricas; la tortilla de maíz pasa de `A004` a `011131`.
- Los precios son corrientes (sin deflactar) y proceden del gasto declarado, no de precios de mercado.

## Validaciones

Años esperados presentes; `kg_dia_hogar` nacional dentro de ±2% de valores de control; precio implícito entre 5 y 60 pesos/kg; porcentajes entre 0 y 100; 32 entidades y 10 deciles por año; sin duplicados en `anio`–`nivel`–`clave_nivel`.
