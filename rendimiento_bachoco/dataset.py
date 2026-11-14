from typing import Annotated, Callable

from loguru import logger
from tqdm import tqdm
import typer

from rendimiento_bachoco.config import (
    INTERIM_DATA_DIR,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    REFERENCES_DIR,
    INDICATORS_INEGI,
    DGSIAP_START_YEAR,
    DGSIAP_END_YEAR,
)
from rendimiento_bachoco.quality.yahoo import validate_finance_monthly, validate_finance_raw
from rendimiento_bachoco.quality.inegi import validate_inegi
from rendimiento_bachoco.quality.conasami import validate_conasami
from rendimiento_bachoco.quality.dgsiap import validate_dgsiap
from rendimiento_bachoco.quality.enigh import validate_enigh
from rendimiento_bachoco.quality.inpc import validate_inpc
from rendimiento_bachoco.quality.profeco import validate_profeco
from rendimiento_bachoco.sources.conasami import download_conasami, process_conasami
from rendimiento_bachoco.sources.dgsiap import (
    download_dgsiap,
    process_dgsiap,
    process_dgsiap_metadata,
)
from rendimiento_bachoco.sources.enigh import (
    ENIGH_PROCESSED_PATH,
    ENIGH_RAW_DIR,
    download_enigh,
    process_enigh,
)
from rendimiento_bachoco.sources.profeco import (
    INTERIM_PATH as PROFECO_INTERIM_PATH,
    PROCESSED_PATH as PROFECO_PROCESSED_PATH,
    PROFECO_RAW_DIR,
    download_profeco,
    process_profeco,
)
from rendimiento_bachoco.sources.inegi import download_inegi_data, process_inegi_data
from rendimiento_bachoco.sources.inpc import INPC_INDICADORES, download_inpc, process_inpc
from rendimiento_bachoco.sources.sniim import download_sniim_data
from rendimiento_bachoco.sources.yahoo import download_finance_data, process_finance_data

CONASAMI_RAW_PATH = RAW_DATA_DIR / "CONASAMI" / "salarios_minimos_2009_2026.xlsx"
CONASAMI_PROCESSED_PATH = PROCESSED_DATA_DIR / "salario_minimo_mensual.csv"
INPC_RAW_DIR = RAW_DATA_DIR / "INEGI" / "INPC"
INPC_PROCESSED_PATH = PROCESSED_DATA_DIR / "inpc_mensual.csv"

app = typer.Typer()


def _run_steps(steps: dict[str, Callable[[], None]], description: str) -> list[str]:
    failed: list[str] = []
    for name, step in tqdm(steps.items(), total=len(steps), desc=description):
        try:
            step()
        except Exception:
            # Un paso que falla no detiene a los demás.
            logger.exception(f"\t{description} falló: {name}")
            failed.append(name)
    return failed


@app.command()
def main(
    only: Annotated[
        str | None,
        typer.Option(help="Corre solo los pasos de una fuente (p. ej. CONASAMI, PROFECO, ENIGH, INPC)."),
    ] = None,
) -> None:

    # Git no versiona carpetas vacías: se crean las de datos.
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
            data_root=RAW_DATA_DIR, indicators=INDICATORS_INEGI
        ),
        "DGSIAP": lambda: download_dgsiap(
            output_path=RAW_DATA_DIR / "DGSIAP",
            start_year=DGSIAP_START_YEAR,
            end_year=DGSIAP_END_YEAR,
        ),
        "CONASAMI": lambda: download_conasami(CONASAMI_RAW_PATH),
        "PROFECO": lambda: download_profeco(PROFECO_RAW_DIR),
        "ENIGH": lambda: download_enigh(ENIGH_RAW_DIR),
        "INPC": lambda: download_inpc(INPC_RAW_DIR, INPC_INDICADORES),
    }

    # SNIIM se procesa aparte en rendimiento_bachoco/process_sniim.py (ver README).
    process_raw_data: dict[str, Callable[[], None]] = {
        "Finance data (monthly returns)": lambda: process_finance_data(
            RAW_DATA_DIR / "RendimientoYahoo", INTERIM_DATA_DIR
        ),
        "INEGI indicators and metadata to tidy format": lambda: process_inegi_data(
            inegi_raw_dir=RAW_DATA_DIR / "INEGI",
            inegi_tidy_dir=INTERIM_DATA_DIR / "INEGI",
            indicators=INDICATORS_INEGI,
        ),
        "DGSIAP": lambda: process_dgsiap(
            raw_dir=RAW_DATA_DIR / "DGSIAP", tidy_dir=INTERIM_DATA_DIR / "DGSIAP"
        ),
        "DGSIAP metadata": lambda: process_dgsiap_metadata(
            raw_dir=RAW_DATA_DIR / "DGSIAP", tidy_dir=INTERIM_DATA_DIR / "DGSIAP"
        ),
        "CONASAMI": lambda: process_conasami(CONASAMI_RAW_PATH, CONASAMI_PROCESSED_PATH),
        "PROFECO": lambda: process_profeco(
            PROFECO_RAW_DIR, PROFECO_PROCESSED_PATH.parent, PROFECO_INTERIM_PATH
        ),
        "ENIGH": lambda: process_enigh(ENIGH_RAW_DIR, ENIGH_PROCESSED_PATH),
        "INPC": lambda: process_inpc(INPC_RAW_DIR, INPC_PROCESSED_PATH),
    }

    # Solo la fuente financiera tiene validación de calidad por ahora.
    validate_processed_data: dict[str, Callable[[], None]] = {
        "Finance data (raw schema)": lambda: validate_finance_raw(
            RAW_DATA_DIR / "RendimientoYahoo"
        ),
        "Finance data (monthly schema)": lambda: validate_finance_monthly(
            INTERIM_DATA_DIR / "rendimiento_mensual.parquet"
        ),
        "Metadatos INEGI (tidy)": lambda: validate_inegi(
            raw_path=INTERIM_DATA_DIR / "inegi_metadata.csv", meta=True
        ),
        "Datos INEGI (tidy)": lambda: validate_inegi(
            raw_path=INTERIM_DATA_DIR / "inegi_data.csv", meta=False
        ),
        "Datos DGSIAP (tidy)": lambda: validate_dgsiap(
            raw_dir=INTERIM_DATA_DIR / "DGSIAP",
            meta_filepath=INTERIM_DATA_DIR / "DGSIAP" / "dgsiap_metadata.csv",
        ),
        "CONASAMI (tidy)": lambda: validate_conasami(CONASAMI_PROCESSED_PATH),
        "PROFECO (tidy)": lambda: validate_profeco(PROFECO_PROCESSED_PATH),
        "ENIGH (tidy)": lambda: validate_enigh(ENIGH_PROCESSED_PATH),
        "INPC (tidy)": lambda: validate_inpc(INPC_PROCESSED_PATH),
    }

    if only:

        def _filtrar(steps: dict[str, Callable[[], None]]) -> dict[str, Callable[[], None]]:
            return {k: v for k, v in steps.items() if k.upper().startswith(only.upper())}

        download_raw_data = _filtrar(download_raw_data)
        process_raw_data = _filtrar(process_raw_data)
        validate_processed_data = _filtrar(validate_processed_data)

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
