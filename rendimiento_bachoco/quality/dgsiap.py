from pandera.pandas import Check, Column, DataFrameSchema
from rendimiento_bachoco.config import REFERENCES_DIR, RAW_DATA_DIR, DGSIAP_START_YEAR, DGSIAP_END_YEAR
from pathlib import Path
from loguru import logger
import pandas as pd
import pandera as pa

def get_df_schema(meta_path: Path) -> DataFrameSchema:
    meta_df = pd.read_csv(REFERENCES_DIR / "dgsiap_metadata.csv")
    
    meta_df.columns = meta_df.iloc[8, 0:]
    symb_sr = meta_df.loc[34:38, 'Consecutivo\nen la base']
    symb_dict = {x[0] : x[1] for x in symb_sr.str.strip().str.split(':')}
    symb_dict.pop('#')
    symb_dict.pop('A')
    symb_type_dict = {k : t for k, t in zip(symb_dict.keys(), [str, int, float])} # {'T': str, 'N': int, 'D': float}

    meta_df = meta_df.drop(columns = ['Unnamed: 0.1'], errors = 'ignore')
    meta_df = meta_df.iloc[9:33].reset_index()
    meta_df = meta_df.reset_index().drop(columns = ['index', 'level_0'])
    meta_df = meta_df.rename(columns = {'Nombre\nde campo' : 'NombreCampo', 'Consecutivo\nen la base' : 'ConsecutivoBase'})

    # Los nombres: 'Nomcultivo'/'Nomcultivo' y 'Precio'/'Preciomediorural' son inconsistentes en diferentes años así que se haces manualmente
    meta_df = meta_df.loc[
        (meta_df['NombreCampo'] != 'Precio') & 
        (meta_df['NombreCampo'] != 'Nomcultivo') &
        (meta_df['NombreCampo'] != 'Rendimiento') & # 2024 fiasco
        (meta_df['NombreCampo'] != 'Preciomediorural') # 2024 fiasco
        ].reset_index()

    # Construyendo el Schema a partir de los metadatos
    schema_columns_dict = {
        name : Column(symb_type_dict[entry_type], 
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
        logger.info(f"Validando {year}...")
        dgsiap_df = pd.read_csv(raw_dir / f'{year}.csv', index_col = 0)
        dgsiap_raw_schema.validate(dgsiap_df)
        logger.success(f'{year} validado.')


    logger.success(f'Datos DGSIAP validados: {raw_dir}')


