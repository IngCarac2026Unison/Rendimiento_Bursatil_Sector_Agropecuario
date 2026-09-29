from pathlib import Path
from loguru import logger
import pandas as pd
from pandera.pandas import Check, Column, DataFrameSchema
import pandera as pa
from rendimiento_bachoco.sources.inegi import get_state_dict
from rendimiento_bachoco.config import INDICATORS_INEGI

stateDict: dict = get_state_dict()


inegi_raw_schema = DataFrameSchema(
    columns = {
        # Son str porque no tienen propiedades numéricas, sino sólo son llaves de diccionario
        "INDICADOR" :   Column(str, coerce = True, checks = [
            Check.str_length(10),
            Check.isin(INDICATORS_INEGI)
            ]),
        "FREQ" :        Column(str, coerce = True, checks = Check.isin(['1','3','4','5','6','7','8','9','10','11','16','23','24'])),
        "TOPIC" :       Column(int, Check.in_range(min_value = 0, max_value = 2100)),
        "UNIT" :        Column(int, Check.in_range(min_value = 0, max_value = 10000)),
        "UNIT_MULT" :   Column(str, coerce = True, checks = Check.isin(['1','4','2','-1']), nullable = True),
        "NOTE" :        Column(str, coerce = True, default = '-1', nullable = True),
        "SOURCE" :      Column(int),
        "LASTUPDATE":   Column(pa.DateTime, coerce=True, nullable=True),
        "TIME_PERIOD":  Column(pa.DateTime, coerce=True, nullable=True),
        "OBS_VALUE":    Column(float),
        "OBS_STATUS" :  Column(str, coerce = True, checks = Check.isin(['1','2','3','4','6','7','8'])),
        "COBER_GEO" :   Column(int, coerce = True, checks = Check.isin(range(0, 33))),
    },
    checks = [
        Check(
            lambda df : df.index.is_unique,
            error = 'Index not unique.'
        )
    ],
    strict = False
)

meta_inegi_raw_schema = DataFrameSchema(
    columns = {
        "Indicador" : Column(str, coerce = True , checks = Check.str_length(10)),
        "Descripcion" : Column(str)
    },
    checks = [
        Check(
            lambda df : df['Indicador'].is_unique, 
            error = 'Indicadores duplicados.'
        )
    ],
    strict = False
)



def validate_inegi(raw_path: Path, meta : bool):

    logger.info("Validando datos del INEGI...")

    if not raw_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {raw_path}")
    elif raw_path.is_dir():
        raise IsADirectoryError(f"The filepath passed is a directory: {raw_path}")
    

    df = pd.read_csv(raw_path, dtype={"UNIT_MULT": "str"})

    schema = meta_inegi_raw_schema if meta else inegi_raw_schema

    schema.validate(df)

    logger.success(f'Datos INEGI validados{'(Metadatos)' if meta else ''}: {raw_path}')


