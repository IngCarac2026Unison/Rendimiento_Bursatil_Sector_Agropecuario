from datetime import datetime
from pathlib import Path

from loguru import logger
import pandas as pd


def download_dgsiap(
        output_path : Path,
        start_year: int,
        end_year: int,
):

    Path.mkdir(output_path, parents = True, exist_ok = True)

    logger.info("\tDescargando datos de DGSIAP...")

    meta_df = pd.read_excel("https://nube.agricultura.gob.mx/index.php?view=5D24F995-E734D711-1EA6F8D2-9D1387D7", engine = "openpyxl").to_csv(output_path / f"metadata.xlsx")

    for year in range(start_year, end_year + 1):
        pd.read_csv(f"https://nube.agricultura.gob.mx/index.php?view=10AE434F-A2158368-A120BC5A-EDF4AFAA&ANIO={year}", encoding = "latin1").to_csv(output_path / f"{year}.csv")

    log_text = f'''Datos de DGSIAP descargados el {datetime.now()}'''
    text_log_id = logger.add(output_path / "dgsiap_log.txt")
    logger.info(log_text)
    logger.remove(text_log_id)
