# Diccionario de datos: precios mensuales de maíz blanco

**Archivo:** `data/processed/sniim_maiz_blanco_mensual.csv`  
**Fuente:** Sistema Nacional de Información e Integración de Mercados (SNIIM)  
**Periodo seleccionado:** 2013–2025  
**Unidad de observación:** un mes, mercado y origen del producto.

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha` | fecha | Primer día del mes al que corresponde el precio; no representa una cotización diaria. |
| `estado_mercado` | texto | Entidad federativa donde se ubica el mercado. |
| `mercado` | texto | Ciudad o mercado mayorista seleccionado. |
| `origen` | texto | Procedencia del maíz indicada por el SNIIM; puede diferir de la ubicación del mercado. |
| `producto` | texto | Producto consultado: maíz blanco. |
| `precio_mxn_kg` | decimal | Precio promedio mensual en pesos mexicanos por kilogramo. |

Las celdas vacías de la fuente se conservan como precios faltantes; no equivalen a cero. Un mercado puede tener más de un origen en el mismo mes, por lo que puede haber varias filas con la misma fecha y mercado.

El procesamiento comprueba que las fechas estén entre 2013 y 2025, que no se repita la combinación `fecha`–`mercado`–`origen` y que los precios registrados sean positivos.
