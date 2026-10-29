from pandera.pandas import Check, Column, DataFrameSchema
from pathlib import Path
from loguru import logger
import pandas as pd
import pandera as pa
from rendimiento_bachoco.config import DGSIAP_START_YEAR, DGSIAP_END_YEAR, INTERIM_DATA_DIR
import json


def get_df_schema(meta_path: Path) -> DataFrameSchema:


    meta_df = pd.read_csv(meta_path)
    sym_type_dict = {'T': str, 'N': int, 'D': float} # derivado de /raw/DGSIAP/dgsiap_metadata.csv

    # Los nombres: 'Nomcultivo'/'Nomcultivo Sin Um' y 'Precio'/'Preciomediorural' son inconsistentes en diferentes años así que se hace manualmente
    meta_df = meta_df.loc[
        (meta_df['NombreCampo'] != 'Precio') & 
        (meta_df['NombreCampo'] != 'Nomcultivo') &
        (meta_df['NombreCampo'] != 'Rendimiento') & # 2024 fiasco
        (meta_df['NombreCampo'] != 'Preciomediorural') # 2024 fiasco
        ].reset_index()

    # Construyendo el Schema a partir de los metadatos
    schema_columns_dict = {
        name : Column(sym_type_dict[entry_type], 
                      coerce = True)
            for name, entry_type in zip(meta_df['NombreCampo'], meta_df['Tipo'])}
    
    # El nombre 'Nomcultivo'/'Nomcultivo Sin Um' es inconsistente en diferentes años así que se hace manualmente
    schema_columns_dict['Nomcultivo'] = Column(str, required=False, coerce=True)
    schema_columns_dict['Nomcultivo Sin Um'] = Column(str, required=False, coerce=True)
    
    # El nombre 'Precio'/'Preciomediorural' es inconsistente en diferentes años así que se hace manualmente
    schema_columns_dict['Precio'] = Column(float, required=False, coerce=True)
    schema_columns_dict['Preciomediorural'] = Column(float, required=False, coerce=True)
    
    # 2024
    schema_columns_dict['Rendimiento'] = Column(float, required=False, coerce=True, nullable = True)
    schema_columns_dict['Preciomediorural'] = Column(float, required=False, coerce=True, nullable = True)

    dgsiap_raw_schema = DataFrameSchema(
        columns = schema_columns_dict,
        checks = [
            Check(lambda df : df.index.is_unique, error = 'Índice no es único.'),
        ],
        strict = False
    )


    return dgsiap_raw_schema


def validate_dgsiap(raw_dir: Path, meta_filepath : Path):

    logger.info("Validando datos del DGSIAP...")

    if not raw_dir.exists():
        raise FileNotFoundError(f"No se encontró el directorio: {raw_dir}")
    elif not raw_dir.is_dir():
        raise NotADirectoryError(f"La dirección no es directorio: {raw_dir}")
    

    dgsiap_raw_schema = get_df_schema(meta_filepath)

    for year in  range(DGSIAP_START_YEAR, DGSIAP_END_YEAR + 1):
        # logger.info(f"Validando {year}...")
        dgsiap_df = pd.read_csv(raw_dir / f'{year}.csv', index_col = 0)
        dgsiap_raw_schema.validate(dgsiap_df)
        logger.success(f'{year} validado.')


    logger.success(f'Datos DGSIAP validados: {raw_dir}')


