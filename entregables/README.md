# Entregables por fase

Rutas relativas a la raíz del repositorio (`../`). Estado: **listo**, **en curso** o **pendiente**.

## Fase 1: procesamiento de datos

| Requisito | Estado | Dónde |
|---|---|---|
| Tema, pregunta y tipos de datos | Listo | [README](../README.md) (problemática, pregunta de investigación, tipos de datos) |
| Público destinatario y fuentes primarias | Listo | [README](../README.md) (secciones "Público destinatario" y "Fuentes de datos") |
| Script de descarga de al menos dos fuentes, con descripción y fecha | Listo | [`dataset.py`](../rendimiento_bachoco/dataset.py), [`sources/`](../rendimiento_bachoco/sources/); datos crudos en `data/raw/` (no versionados, se generan con `make data`) |
| Transformación a datos tidy | Listo | [`sources/yahoo.py`](../rendimiento_bachoco/sources/yahoo.py), [`process_sniim.py`](../rendimiento_bachoco/process_sniim.py), [`sources/dgsiap.py`](../rendimiento_bachoco/sources/dgsiap.py); salidas en `data/interim/` y `data/processed/` |
| Diccionarios de datos | Listo | [SNIIM](../references/diccionario_sniim_maiz_blanco.md), [rendimiento mensual](../references/diccionario_rendimiento_mensual.md), [DGSIAP](../references/diccionario_dgsiap.md) |
| Calidad de datos | Listo | [`quality/`](../rendimiento_bachoco/quality/), [validación SNIIM](../references/validacion_sniim.md) |
| Instrucciones de entorno, descarga y procesamiento | Listo | [README](../README.md) (sección "Cómo generar los datos") y [Makefile](../Makefile) |

## Fase 2: análisis exploratorio de datos

| Requisito | Estado | Dónde |
|---|---|---|
| Auto EDA | Listo | [`reports/auto_eda/`](../reports/auto_eda/): [Gruma](../reports/auto_eda/gruma_diario.html), [Minsa](../reports/auto_eda/minsa_diario.html), [rendimiento mensual](../reports/auto_eda/rendimiento_mensual.html), [SNIIM](../reports/auto_eda/sniim_maiz_blanco.html) |
| Libretas de EDA (faltantes, anomalías, relaciones, correlación, PCA y t-SNE) | Listo | [`01-mg-datos_bursatiles`](../notebooks/01-mg-datos_bursatiles.ipynb), [`01-eda-sniim`](../notebooks/01-eda-sniim.ipynb), [`01-eda-dgsiap`](../notebooks/01-eda-dgsiap.ipynb), [`02-eda-sniim-bolsa`](../notebooks/02-eda-sniim-bolsa.ipynb), [`02-mg-cruce-eventos-maiz-sniim-dgsiap`](../notebooks/02-mg-cruce-eventos-maiz-sniim-dgsiap.ipynb); figuras en [`reports/figures/`](../reports/figures/) |
| Consulta con usuarios sobre la exploración | Listo | Recomendaciones incorporadas en la conclusión de [hallazgos](fase2/hallazgos.md) |
| Reporte de hallazgos (máx. 3 páginas de detalle) | Listo | [md](fase2/hallazgos.md), [html](fase2/hallazgos.html), [pdf](fase2/hallazgos.pdf) (4 páginas: portada con resumen y 3 de detalle) |
| Presentación (menos de 5 minutos y de 5 slides) | Listo | [html](../reports/presentacion/presentacion_hallazgos.html), [pdf](../reports/presentacion/presentacion_hallazgos.pdf), [guion](../reports/presentacion/guion.md) |

## Fase 3: historia con datos

| Requisito | Estado | Dónde |
|---|---|---|
| Borrador de historias | Listo | [`reports/historia/`](../reports/historia/borrador_historias.md) |
| Historia 1: ¿Quién paga el maíz caro? | Listo | [html](fase3/historia1.html); libreta [`05-mg-cadena-maiz-tortilla`](../notebooks/05-mg-cadena-maiz-tortilla.ipynb); figuras con `make historia1` ([`historia1.py`](../rendimiento_bachoco/historia1.py), [`plots.py`](../rendimiento_bachoco/plots.py)) en [`reports/figures/`](../reports/figures/) |
| Presentación de la historia 1 | Listo | [html](fase3/historia1_presentacion.html), [guion](fase3/guion_historia1.md) |
