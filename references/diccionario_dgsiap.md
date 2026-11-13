# Diccionario de datos: producción agrícola DGSIAP

**Archivos:** `data/raw/DGSIAP/<año>.csv` (crudo) y `data/interim/DGSIAP/<año>.csv` (filtrado por cultivo)  
**Fuente:** Dirección General del Servicio de Información Agroalimentaria y Pesquera (DGSIAP), Secretaría de Agricultura y Desarrollo Rural. Datos abiertos de cierre del año agrícola: https://nube.agricultura.gob.mx/datosAbiertos/Agricola.php  
**Cobertura disponible:** 2018–2025, un archivo por año (el rango configurado en `config.py` empieza en 2013, pero los archivos descargados cubren desde 2018).  
**Unidad de observación:** un municipio, ciclo productivo, modalidad hídrica y cultivo, en un año. Cada archivo tiene entre 28,661 y 38,696 filas y 24 columnas (más la columna de índice que agrega la descarga).

Los archivos de metadatos `data/raw/DGSIAP/metadata.xlsx` (en realidad CSV) y `dgsiap_metadata.csv` reproducen la descripción oficial de campos.

## Columnas

| Columna | Tipo | Descripción |
|---|---|---|
| `Anio` | entero | Año agrícola de la información. |
| `Idestado` | entero | Clave de la entidad federativa (1 a 32, orden alfabético INEGI). |
| `Nomestado` | texto | Nombre de la entidad federativa. 32 en todos los años. |
| `Idddr` | entero | Clave del Distrito de Desarrollo Rural. |
| `Nomddr` | texto | Nombre del Distrito de Desarrollo Rural. |
| `Idcader` | entero | Clave del Centro de Apoyo al Desarrollo Rural. |
| `Nomcader` | texto | Nombre del Centro de Apoyo al Desarrollo Rural. |
| `Idmunicipio` | entero | Clave del municipio dentro de la entidad (no es única a nivel nacional sin `Idestado`). |
| `Nommunicipio` | texto | Nombre del municipio o alcaldía. |
| `Idciclo` | entero | Clave del ciclo: 1 Otoño-Invierno, 2 Primavera-Verano, 3 Perennes. |
| `Nomcicloproductivo` | texto | Nombre del ciclo productivo. |
| `Idmodalidad` | entero | Clave de la modalidad hídrica. |
| `Nommodalidad` | texto | `Riego` o `Temporal`. |
| `Idunidadmedida` | entero | Clave de la unidad de medida del cultivo. |
| `Nomunidad` | texto | Unidad del volumen: `Tonelada` en la mayoría; también `Metro cuadrado`, `Gruesa`, `Planta`, `Manojo` y `Miles de lts.` en cultivos particulares. |
| `Idcultivo` | entero | Clave del cultivo en el catálogo DGSIAP. |
| `Nomcultivo` | texto | Nombre del cultivo (por ejemplo, `Maíz grano`). Se llama `Nomcultivo Sin Um` en 2018–2020. No distingue maíz blanco de amarillo. |
| `Sembrada` | decimal | Superficie sembrada, en hectáreas. |
| `Cosechada` | decimal | Superficie cosechada, en hectáreas. |
| `Siniestrada` | decimal | Superficie siniestrada (sin producción por pérdida), en hectáreas. |
| `Volumenproduccion` | decimal | Volumen de producción, en toneladas (salvo las unidades especiales de `Nomunidad`). |
| `Rendimiento` | decimal | Toneladas por hectárea cosechada (salvo unidades especiales). |
| `Precio` | decimal | Precio medio rural, en MXN por tonelada. Se llama `Preciomediorural` desde 2021. |
| `Valorproduccion` | decimal | Valor de la producción, en pesos corrientes. |

## Rangos y faltantes (2018–2025 combinados)

| Columna | Mínimo | Máximo | Faltantes | Ceros |
|---|---|---|---|---|
| `Sembrada` | 0 | 179,125.5 | 0 | 60 |
| `Cosechada` | 0 | 179,125.5 | 0 | 3,333 |
| `Siniestrada` | 0 | 54,073 | 0 | 270,359 |
| `Volumenproduccion` | 0 | 118,300,000 | 0 | 3,333 |
| `Rendimiento` | 0 | 5,862,000 | 873 | 2,460 |
| `Precio` | 0 | 1,200,000 | 873 | 2,460 |
| `Valorproduccion` | 0 | 7.6e9 | 0 | 3,333 |

- Los máximos de `Rendimiento` y `Precio` corresponden a cultivos con unidades distintas de la tonelada; para comparar entre cultivos hay que filtrar por `Nomunidad == "Tonelada"`.
- Un precio o volumen en cero corresponde a superficie siniestrada o sin cosecha, no a ventas a precio cero.
- Los faltantes de `Rendimiento` y `Precio` aparecen solo en 2024 (458 filas) y 2025 (415 filas).

## Inconsistencias entre años

- `Nomcultivo` se llama `Nomcultivo Sin Um` en 2018–2020; `Precio` se llama `Preciomediorural` desde 2021.
- En algunos años (por ejemplo, 2021 y 2022) `Sembrada` o `Volumenproduccion` llegan como texto con separador de miles (`1,234.5`).
- El número de cultivos distintos cambia mucho entre años (de unos 80 en 2020–2021 a más de 300 en el resto) por cambios de catálogo; el maíz grano se mantiene estable, con 4,558 a 4,669 filas por año.

## Procesamiento

`rendimiento_bachoco/sources/dgsiap.py` (`process_dgsiap`) quita las comas de miles en `Sembrada` y `Volumenproduccion`, las convierte a decimal y conserva solo los cultivos relacionados con la actividad de Gruma: `Maíz grano`, `Maíz forrajero en verde`, `Trigo grano`, `Trigo forrajero verde`, `Arroz palay`, `Avena grano`, `Semilla de avena grano`, `Avena forrajera en verde`, `Avena forrajera achicalada` y `Avena forrajera seca`. El resultado se guarda en `data/interim/DGSIAP/<año>.csv`. `process_dgsiap_metadata` deja la descripción de campos en `data/interim/DGSIAP/dgsiap_metadata.csv`.

## Reglas de calidad

`rendimiento_bachoco/quality/dgsiap.py` construye un esquema pandera a partir de los metadatos oficiales (tipos `T`, `N`, `D`) y valida cada archivo tidy: tipos de columna con conversión, tolerancia a los dos nombres de `Nomcultivo` y `Precio`, `Rendimiento` y `Precio` con faltantes permitidos, e índice único.
