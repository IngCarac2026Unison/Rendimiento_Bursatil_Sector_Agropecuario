<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>


# Rendimiento bursátil de Gruma
Proyecto dedicado al proyecto de la materia de Ingenieria de Caracteristicas en la maestria de Ciencia de Datos.

> Estado: propuesta preliminar sujeta a validación de disponibilidad y calidad de los datos.

## Problemática
El *maíz* constituye uno de los principales insumos utilizados en la elaboración de harina de maíz y también de las *tortillas*. Tener variaciones de sus precios pueden representar cambios en los costos y en las condiciones del mercado en el que participa la empresa **Gruma**.

Los precios del maíz representan variacioens temporales y regionales entre los diferentes mercados mayoristas del país. En este proyecto, se busca integrar estos datos con el compartamiento histórico de las acciones de Gruma. 

## Pregunta de investigación
¿Qué relación tuvieron las variaciones de los precios regionales del maíz en México con los rendimientos mensuales de las acciones de Gruma en la Bolsa Mexicana de Valores entre 2013 y 2025?

Esta investigación tiene un alcance descriptivo y exploratorio, por lo cual los hallazgos no se interpretaran como causales.

## Fuentes de datos preliminares

### Bolsa Mexicana de Valores y Yahoo Finance

Se utilizarán para consultar y validar los precios históricos de las acciones Serie B de Gruma. La clave de cotización es `GRUMA B` en la Bolsa Mexicana de Valores y `GRUMAB.MX` en Yahoo Finance.

- Bolsa Mexicana de Valores: https://www.bmv.com.mx/es/emisoras/perfil/-5454
- Yahoo Finance: https://finance.yahoo.com/quote/GRUMAB.MX/

### Sistema Nacional de Información e Integración de Mercados

El SNIIM, perteneciente a la Secretaría de Economía, publica precios del maíz en mercados mayoristas de distintas ciudades y estados de México.

- https://www.economia-sniim.gob.mx/analisis/Precios.asp

Esta fuente contiene información temporal, cuantitativa, cualitativa y geográfica, como fecha, mercado, ciudad, estado, variedad, presentación y precio.

### Fuentes complementarias: DGSIAP

Como posible fuente complementaria se evaluarán los datos abiertos de producción de maíz por estado y municipio.

- https://nube.agricultura.gob.mx/datosAbiertos/Agricola.php

### Fuentes complementarias: INEGI

Adicionalmente se analizan una variedad de indicadores de la base de datos abierta del Instituto Nacional de Estadística y Geografía (INEGI)

- https://www.inegi.org.mx/servicios/api_indicadores.html

## Tipos de datos

- **Series de tiempo:** precios de la acción y precios del maíz.
- **Datos geográficos:** mercados, ciudades, estados y municipios.
- **Datos cuantitativos:** precios, volúmenes y rendimientos bursátiles.
- **Datos cualitativos:** producto, variedad, presentación y mercado.

## Procesamiento de precios del SNIIM

Desde la raíz del repositorio, instala las dependencias con `uv sync`. La descarga
general se ejecuta con `uv run python rendimiento_bachoco/dataset.py` (o `make data`
si tienes `make` instalado). Ese comando descarga todas las fuentes del proyecto;
la parte del INEGI requiere su propia clave de API.

Cuando existan los cinco archivos `data/raw/sniim_*_maiz_blanco.html`, transforma
los precios del maíz blanco con:

```bash
uv run python rendimiento_bachoco/process_sniim.py
```

Si tienes `make`, el comando equivalente es `make process_sniim`. El resultado es
`data/processed/sniim_maiz_blanco_mensual.csv`: una fila por mes, mercado y origen
del maíz, entre 2013 y 2025. Las celdas vacías conservan el precio como dato
faltante. El script comprueba fechas, claves duplicadas y precios no positivos.
Consulta `references/diccionario_sniim_maiz_blanco.md` para la descripción de
cada columna.

## Project Organization

```
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- A default mkdocs project; see www.mkdocs.org for details
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         rendimiento_bachoco and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for flake8
│
└── rendimiento_bachoco   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes rendimiento_bachoco a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    ├── features.py             <- Code to create features for modeling
    │
    ├── modeling                
    │   ├── __init__.py 
    │   ├── predict.py          <- Code to run model inference with trained models          
    │   └── train.py            <- Code to train models
    │
    └── plots.py                <- Code to create visualizations
```

--------

