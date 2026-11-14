# Diccionario de datos: salario mínimo mensual

**Archivo:** `data/processed/salario_minimo_mensual.csv`  
**Fuente:** Comisión Nacional de los Salarios Mínimos (CONASAMI), [consulta de salarios mínimos](https://www.gob.mx/conasami/documentos/consulta-de-salarios-minimos)  
**Periodo:** enero de 2013 a diciembre de 2025 (se extiende a 2026 si la fuente tiene vigencias de ese año)  
**Unidad de observación:** un mes y un área salarial.

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha` | fecha | Primer día del mes. |
| `zona_original` | texto | Zona de la fuente de la que proviene el valor: `b`, `unica`, `restodelpais`, `zsmg` o `zlfn`. |
| `area` | texto | `general` (resto del país) o `zlfn` (Zona Libre de la Frontera Norte). |
| `salario_minimo_diario_mxn` | decimal | Salario mínimo general vigente al primer día del mes, en pesos mexicanos por día, redondeado a 2 decimales. |

## Definición de `area`

La clasificación de zonas cambió con el tiempo, por lo que `general` se arma con la zona que cubre la mayor parte del país en cada periodo:

| Periodo | Zona original de `general` |
|---|---|
| ene 2013 – sep 2015 | `b` (la zona B cubría la mayor parte del país; la zona A era la de mayor salario) |
| oct 2015 – dic 2018 | `unica` (unificación de zonas A y B) |
| 2019 – 2024 | `restodelpais` |
| 2025 en adelante | `zsmg` (zona de salario mínimo general) |

`zlfn` existe desde enero de 2019.

## Notas

- La fuente registra cambios de vigencia, no valores mensuales. El valor de cada mes es el vigente al primer día del mes (se arrastra el último cambio). 2018 no tiene fila porque siguió vigente el salario de diciembre de 2017.
- Los incrementos intermedios en un mes (p. ej. 1 de abril de 2015) se reflejan desde el mes siguiente.
- Las vigencias originales de todas las zonas se guardan en `data/interim/CONASAMI/vigencias_salario_minimo.csv`.
- El archivo de la fuente incluye también salarios profesionales; no se usan.
- Diccionario oficial: <https://www.gob.mx/cms/uploads/attachment/file/876086/Salarios_Minimos_Generales_y_Profesionales_2009_2026_Zonas_DiccionarioDeDatos.xlsx>

El procesamiento y la validación comprueban que no se repita `fecha`–`area`, que los meses sean continuos, que los valores sean positivos y no decrecientes, y que coincidan con valores de control de la fuente.
