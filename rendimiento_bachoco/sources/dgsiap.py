from datetime import datetime
from pathlib import Path
import json 
from loguru import logger
import pandas as pd
from rendimiento_bachoco.config import RAW_DATA_DIR, INTERIM_DATA_DIR, DGSIAP_START_YEAR, DGSIAP_END_YEAR

def process_dgsiap_metadata(raw_dir: Path,   #raw
                            tidy_dir: Path):
    meta_df = pd.read_csv(raw_dir / "dgsiap_metadata.csv")
    meta_df.columns = meta_df.iloc[8, 0:]
    symb_sr = meta_df.loc[34:38, 'Consecutivo\nen la base']

    # meta_df = meta_df.drop(columns = ['Unnamed: 0.1'])
    meta_df = meta_df.iloc[9:33].reset_index()
    meta_df = meta_df.reset_index().drop(columns = 'index')
    meta_df = meta_df.rename(columns = {'Nombre\nde campo' : 'NombreCampo', 'Consecutivo\nen la base' : 'ConsecutivoBase'})
    meta_df = meta_df.drop(columns = ['level_0', 'ConsecutivoBase', 8])
    meta_df.index = meta_df.index.rename('')
    meta_df.to_csv(tidy_dir / "dgsiap_metadata.csv")
    


def process_dgsiap(raw_dir: Path, 
                   tidy_dir: Path):
    Path.mkdir(tidy_dir, parents = True, exist_ok = True)

    logger.info("Procesando datos de DGSIAP...")
    for year in  range(DGSIAP_START_YEAR, DGSIAP_END_YEAR + 1):
        logger.info(f"Procesando {year}...")
        dgsiap_df = pd.read_csv(raw_dir / f'{year}.csv', index_col = 0)

        # Unas inconsistencias en algunos años (2021...)
        dgsiap_df['Sembrada'] = dgsiap_df['Sembrada'].astype(str).str.replace(',', '', regex=True).astype(float) 
        dgsiap_df['Volumenproduccion'] = dgsiap_df['Volumenproduccion'].astype(str).str.replace(',', '', regex=True).astype(float) 

        nomCultCol = 'Nomcultivo' if 'Nomcultivo' in dgsiap_df.columns else 'Nomcultivo Sin Um'
        dgsiap_df = dgsiap_df.loc[dgsiap_df[nomCultCol].isin(['Maíz grano', 'Maíz forrajero en verde', 'Trigo forrajero verde', 'Trigo grano', \
            'Arroz palay', 'Avena forrajera en verde', 'Avena grano', 'Semilla de avena grano', 'Avena forrajera achicalada', 'Avena forrajera seca'])] # Granos que produce GRUMA: Maíz, trigo, arroz, avena.

        dgsiap_df.to_csv(tidy_dir / f'{year}.csv')

    logger.success("Datos DGISAP procesados.")


def download_dgsiap(
        output_path : Path,
        start_year: int,
        end_year: int,
        force = False
):
    meta_output_file =  output_path / "dgsiap_metadata.csv"
    Path.mkdir(output_path, parents = True, exist_ok = True)

    logger.info("\tDescargando datos de DGSIAP...")
    if not meta_output_file.exists() or force:
        pd.read_excel("https://nube.agricultura.gob.mx/index.php?view=5D24F995-E734D711-1EA6F8D2-9D1387D7", engine = "openpyxl").to_csv(meta_output_file)

    else:
        logger.info(f"Requerimiento de descarga previamente satisfecho: {meta_output_file}")


    for year in range(start_year, end_year + 1):
        data_output_file = output_path / f"{year}.csv"
        if not data_output_file.exists() or force:
            pd.read_csv(f"https://nube.agricultura.gob.mx/index.php?view=10AE434F-A2158368-A120BC5A-EDF4AFAA&ANIO={year}", encoding = "latin1").to_csv(data_output_file)
            
        else:
            logger.info(f"Requerimiento de descarga previamente satisfecho: {data_output_file}")

    log_text = f'''Datos de DGSIAP descargados el {datetime.now()}'''
    text_log_id = logger.add(output_path / "dgsiap_log.txt")
    logger.info(log_text)
    logger.remove(text_log_id)
