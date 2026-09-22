from pathlib import Path
from typing import Callable

from loguru import logger
from tqdm import tqdm
import typer
import yfinance as yf
import requests

from rendimiento_bachoco.config import PROCESSED_DATA_DIR, RAW_DATA_DIR

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

    logger.success(f"Tabla SNIIM guardada en: {output_path}")




@app.command()
def main() -> None:

    # Git doesn't track empty folders, so make sure the data folders exist.
    for directory in (RAW_DATA_DIR, PROCESSED_DATA_DIR):
        directory.mkdir(parents=True, exist_ok=True)

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
