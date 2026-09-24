from pathlib import Path
from typing import Callable, List


from datetime import datetime, timezone

from loguru import logger
from tqdm import tqdm
import typer
import yfinance as yf
import requests
import pandas as pd

from rendimiento_bachoco.config import PROCESSED_DATA_DIR, RAW_DATA_DIR, INEGI_API_KEY
import urllib.request
import json

app = typer.Typer()


def download_finance_data(
    output_path: Path,
    ticker: str = "GRUMAB.MX",
    period: str = "max",
) -> None:
    """
    Download the data from YAHOO Finance and save it to the output path.
    """
    logger.info(f"Downloading {ticker} from YAHOO Finance to {output_path}...")

    data = yf.Ticker(ticker).history(period=period)
    if data.empty:
        raise ValueError(f"YAHOO Finance returned no data for {ticker}")

    data.to_csv(output_path)
    logger.success(f"YAHOO Finance data downloaded successfully: {output_path}")


def download_sniim_data(
    output_path: Path,
    market_code: str = "100",
    market_name: str = "Iztapalapa",
) -> None:
     
    logger.info(f"Descargando maíz blanco de {market_name}...")
    url = (
        "http://www.economia-sniim.gob.mx/"
        "SNIIM-AN/estadisticas/anuariosgran1.asp"
    )

   

    response = requests.post(
        url,
        data={
            "cent": market_code,
            "prod": "OMABLAN",
            "ACCION": "Aceptar",
        },
        timeout=60,
    )
    response.raise_for_status()

    if market_name not in response.text or "2013" not in response.text:
        raise ValueError(f"El SNIIM no devolvió la tabla esperada de {market_name}.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    metadata = (
        "Fuente: Sistema Nacional de Información e Integración de Mercados (SNIIM)\n"
        f"URL de consulta: {url}\n"
        f"URL de respuesta: {response.url}\n"
        f"Fecha de descarga (UTC): {datetime.now(timezone.utc).isoformat()}\n"
        f"Mercado: {market_name}\n"
        f"Código del mercado: {market_code}\n"
        "Producto: Maíz blanco (OMABLAN)\n"
        "Unidad: Pesos mexicanos por kilogramo\n"
        "Frecuencia: Promedios mensuales\n"
        "Contenido: Tabla histórica original en formato HTML, sin filtrar años.\n"
        "Origen: Procedencia del producto; distinto de la ubicación del mercado.\n"
        "Valores faltantes: Las celdas vacías no representan precios de cero.\n"
        f"Archivo de datos: {output_path.name}\n"
    )
    output_path.with_suffix(".txt").write_text(metadata, encoding="utf-8")

    logger.success(f"Tabla SNIIM guardada en: {output_path}")

def url_call(url:str, dst:Path):
    try:
        if not dst.exists():
            urllib.request.urlretrieve(url, dst)

    except urllib.error.HTTPError as e:
        raise ValueError(e)

def get_state_dict():
    
    dict_url: str = f'https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/CL_GEO_AREA/0/es/BISE/2.0/{str(INEGI_API_KEY)}?type=json'
    dict_dir = RAW_DATA_DIR / 'INEGI' / 'MX_state_dict.json'
    dict_dst = dict_dir / 'MX_state_dict.json'

    Path.mkdir(dict_dir, parents = True, exist_ok = True)
    url_call(dict_url, dict_dst)

    stateDict = dict()

    with dict_dst.open('r') as fp:
        stateList = json.load(fp)['CODE']
        for s in stateList:
            stateDict[s['value']] = s['Description']

    # Delete 'Otros estados', 'Extranjero' and 'No especificada'
    del stateDict['35']
    del stateDict['36']
    del stateDict['39']

    return stateDict

# Done like this because INEGI API does not authorize batch calls.
def download_inegi_data(
        data_root : Path,
        indicators: List[str]
):
    
    stateDict: dict = get_state_dict()

    by_state_indicators = ['6207095692', '6207095719']

    data_arg = 'INDICATOR'
    meta_arg = 'CL_INDICATOR'

    meta_dst_dir = Path(RAW_DATA_DIR / 'INEGI' / 'METADATA')


    for indicator in indicators:

        Path.mkdir(meta_dst_dir, parents = True, exist_ok = True)
        meta_src = f'https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/{meta_arg}/{indicator}/es/BISE/2.0/{str(INEGI_API_KEY)}?type=json'
        meta_dst = meta_dst_dir / (indicator + '.json')
        url_call(meta_src, meta_dst)

        if indicator in by_state_indicators:
            for sCode in stateDict.keys():

                dest_dir = data_root / 'INEGI' / indicator
                Path.mkdir(dest_dir, parents = True, exist_ok = True)
                data_src = f'https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/{data_arg}/{indicator}/es/{sCode}/false/BISE/2.0/{INEGI_API_KEY}?type=json'
                data_dst = dest_dir / (sCode + '.json')

                try:
                    url_call(data_src, data_dst)
                    
                except urllib.error.HTTPError as e:
                    if e.code == 400:
                        logger.error(f'Got error: {e}. Make sure your indicator has state-by-state information. Skipping indicator.')
                        break
        else:
            dest_dir = data_root / 'INEGI' / indicator
            Path.mkdir(dest_dir, parents = True, exist_ok = True)
            data_src = f'https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/{data_arg}/{indicator}/es/0/false/BISE/2.0/{INEGI_API_KEY}?type=json'
            data_dst = dest_dir / '0.json'
            try:
                url_call(data_src, data_dst)    
            except urllib.error.HTTPError as e:
                raise(e)
            



def download_dgsiap(
        output_path : Path,
        start_year: int,
        end_year: int,
):
    
    Path.mkdir(output_path, parents = True, exist_ok = True)

    logger.info(f"Downloading data from DGSIAP")

    meta_df = pd.read_excel("https://nube.agricultura.gob.mx/index.php?view=5D24F995-E734D711-1EA6F8D2-9D1387D7", engine = "openpyxl").to_csv(output_path / f"metadata.xlsx")
    
    for year in range(start_year, end_year + 1):
        pd.read_csv(f"https://nube.agricultura.gob.mx/index.php?view=10AE434F-A2158368-A120BC5A-EDF4AFAA&ANIO={year}", encoding = "latin1").to_csv(output_path / f"{year}.csv")

    log_text = f'''DGSIAP Info downloaded on {datetime.now()}'''
    text_log_id = logger.add(output_path / "dgsiap_log.txt")
    logger.info(log_text)
    logger.remove(text_log_id)






@app.command()
def main() -> None:

    # Git doesn't track empty folders, so make sure the data folders exist.
    for directory in (RAW_DATA_DIR, PROCESSED_DATA_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    inegi_indicators = ['6207077700', '6207077710', '6207077719', '6207077733', 
                          '6207077741', '6207077743', '6207077748', '6207129563', 
                          '6207129580', '6207129584', '6207129594','6207129595',
                          '6207129600','6207129608','6207129609', '6207095692',
                          '6207095711','6207095719','6207129821']

    # Each entry is "name of the task": function with no arguments.
    # To add a new source, write its download function and add one line here.
    download_raw_data: dict[str, Callable[[], None]] = {
        "Finance data (YAHOO Finance)": lambda: download_finance_data(
            RAW_DATA_DIR / "rendimiento_acciones.csv"
        ),
                        "SNIIM Hermosillo": lambda: download_sniim_data(
            RAW_DATA_DIR / "sniim_hermosillo_maiz_blanco.html",
            market_code="260",
            market_name="Hermosillo",
        ),
        "SNIIM Culiacán": lambda: download_sniim_data(
            RAW_DATA_DIR / "sniim_culiacan_maiz_blanco.html",
            market_code="250",
            market_name="Culiacán",
        ),
        "SNIIM Guadalajara": lambda: download_sniim_data(
            RAW_DATA_DIR / "sniim_guadalajara_maiz_blanco.html",
            market_code="140",
            market_name="Guadalajara",
        ),
        "SNIIM Iztapalapa": lambda: download_sniim_data(
            RAW_DATA_DIR / "sniim_iztapalapa_maiz_blanco.html",
            market_code="100",
            market_name="Iztapalapa",
        ),
        "SNIIM Guadalupe": lambda: download_sniim_data(
            RAW_DATA_DIR / "sniim_guadalupe_maiz_blanco.html",
            market_code="191",
            market_name="Guadalupe",
        ),
        "INEGI-Indicators": lambda: download_inegi_data(
            RAW_DATA_DIR,
            inegi_indicators
        ),
        # "Other source": lambda: download_other_source(RAW_DATA_DIR / "other_source.csv"),
        "DGSIAP": lambda: download_dgsiap(
            RAW_DATA_DIR / "DGSIAP",
            2013,
            2025
        )
    }

    logger.info("Downloading raw data...")
    failed: list[str] = []

    for name, download in tqdm(
        download_raw_data.items(),
        total=len(download_raw_data),
        desc="Downloads",
    ):
        try:
            download()
        except Exception:
            # One failing source shouldn't stop the rest.
            logger.exception(f"Download failed: {name}")
            failed.append(name)

    if failed:
        logger.error(f"{len(failed)} download(s) failed: {', '.join(failed)}")
        raise typer.Exit(code=1)

    logger.success("All downloads complete.")





if __name__ == "__main__":
    app()
