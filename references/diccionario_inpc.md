# Diccionario de datos: INPC mensual

**Archivo:** `data/processed/inpc_mensual.csv`  
**Fuente:** Instituto Nacional de Estadística y Geografía (INEGI), Banco de Información Económica (BIE), [API de Indicadores](https://www.inegi.org.mx/servicios/api_indicadores.html), indicador `910392`  
**Periodo:** enero de 2013 al último mes publicado (octubre de 2026 en la descarga actual)  
**Unidad de observación:** un mes y una serie. Cobertura nacional.

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha` | fecha | Primer día del mes. |
| `serie` | texto | Serie del índice. Solo `general` (INPC, índice general). |
| `indice` | decimal | Índice nacional de precios al consumidor, base 2a quincena de julio de 2018 = 100. |
| `var_mensual_pct` | decimal | Variación porcentual respecto al mes anterior, redondeada a 4 decimales. |
| `var_anual_pct` | decimal | Variación porcentual respecto al mismo mes del año anterior, redondeada a 4 decimales. |

## Notas

- Las variaciones se calculan sobre la serie completa descargada (desde 1969) y después se recorta a 2013, por lo que enero de 2013 ya tiene variación mensual y anual.
- El índice es mensual (promedio de las quincenas del mes), por lo que los meses de 2018-07 y 2018-08 quedan alrededor de 100 y no exactamente en 100.
- No se incluyen índices genéricos (tortilla de maíz, maíz) porque el API no los expone con un identificador conocido y verificado; la deflactación y las comparaciones usan solo el índice general.
- La descarga requiere un token del API en la variable de entorno `INEGI_API_KEY`. Los datos crudos y un archivo de metadatos (con `<TOKEN>` en lugar de la clave) se guardan en `data/raw/INEGI/INPC/`.

El procesamiento y la validación comprueban que no se repita `fecha`–`serie`, que los meses sean continuos, que el índice sea positivo y que el índice general ronde 100 en 2018-07/08.
