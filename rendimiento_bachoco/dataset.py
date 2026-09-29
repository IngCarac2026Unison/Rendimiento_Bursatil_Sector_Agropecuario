from typing import Callable

from loguru import logger
from tqdm import tqdm
import typer

from rendimiento_bachoco.config import INTERIM_DATA_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR, REFERENCES_DIR, INDICATORS_INEGI
from rendimiento_bachoco.quality.yahoo import validate_finance_monthly, validate_finance_raw
from rendimiento_bachoco.quality.inegi import validate_inegi
from rendimiento_bachoco.sources.dgsiap import download_dgsiap
from rendimiento_bachoco.sources.inegi import download_inegi_data, process_inegi_data
from rendimiento_bachoco.sources.sniim import download_sniim_data
from rendimiento_bachoco.sources.yahoo import download_finance_data, process_finance_data

app = typer.Typer()


def _run_steps(steps: dict[str, Callable[[], None]], description: str) -> list[str]:
    failed: list[str] = []
    for name, step in tqdm(steps.items(), total=len(steps), desc=description):
        try:
            step()
        except Exception:
            # One failing step shouldn't stop the rest.
            logger.exception(f"\t{description} falló: {name}")
            failed.append(name)
    return failed


@app.command()
def main() -> None:

    # Git doesn't track empty folders, so make sure the data folders exist.
    for directory in (RAW_DATA_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR):
        directory.mkdir(parents=True, exist_ok=True)


    download_raw_data: dict[str, Callable[[], None]] = {
        "Finance data (YAHOO Finance)": lambda: download_finance_data(
            RAW_DATA_DIR / "RendimientoYahoo"
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
            INDICATORS_INEGI
        ),
        "DGSIAP": lambda: download_dgsiap(
            RAW_DATA_DIR / "DGSIAP",
            2013,
            2025
        )
    }

    # SNIIM se procesa aparte en rendimiento_bachoco/process_sniim.py (ver README).
    # INEGI aún no tiene función de procesamiento.
    process_raw_data: dict[str, Callable[[], None]] = {
        "Finance data (monthly returns)": lambda: process_finance_data(
            RAW_DATA_DIR / "RendimientoYahoo", INTERIM_DATA_DIR
        ),
        "INEGI indicators and metadata to tidy format": lambda: process_inegi_data(
            inegi_raw_dir = RAW_DATA_DIR / "INEGI",
            inegi_tidy_dir = INTERIM_DATA_DIR / "INEGI",
            indicators = INDICATORS_INEGI
        )
    }

    # Solo la fuente financiera tiene validación de calidad por ahora.
    validate_processed_data: dict[str, Callable[[], None]] = {
        "Finance data (raw schema)": lambda: validate_finance_raw(
            RAW_DATA_DIR / "RendimientoYahoo"
        ),
        "Finance data (monthly schema)": lambda: validate_finance_monthly(
            INTERIM_DATA_DIR / "rendimiento_mensual.parquet"
        ),
        "Metadatos INEGI (tidy)" : lambda : validate_inegi(
            raw_path = INTERIM_DATA_DIR / 'inegi_metadata.csv',
            meta = True
        ),
        "Datos INEGI (tidy)" : lambda : validate_inegi(
            raw_path = INTERIM_DATA_DIR / 'inegi_data.csv',
            meta = False
        ),
    }

    logger.info("Descargando datos crudos...")
    failed = _run_steps(download_raw_data, "Descargas")

    logger.info("Procesando datos crudos...")
    failed += _run_steps(process_raw_data, "Procesamiento")

    logger.info("Validando calidad de datos...")
    failed += _run_steps(validate_processed_data, "Validación")

    if failed:
        logger.error(f"{len(failed)} paso(s) fallaron: {', '.join(failed)}")
        raise typer.Exit(code=1)

    logger.success("Descarga y procesamiento completados.")


if __name__ == "__main__":
    app()
