from datetime import datetime
from pathlib import Path

from loguru import logger
import pandas as pd
from rendimiento_bachoco.config import INTERIM_DATA_DIR


def download_dgsiap(
        output_path : Path,
        start_year: int,
        end_year: int,
        force = False
):
    meta_output_file = INTERIM_DATA_DIR / "metadata.csv"
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
