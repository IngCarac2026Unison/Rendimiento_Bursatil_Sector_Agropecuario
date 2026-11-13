from datetime import UTC, datetime
from pathlib import Path

from loguru import logger
import pandas as pd
import requests

from rendimiento_bachoco.config import INTERIM_DATA_DIR

CONASAMI_URL = (
    "https://www.gob.mx/cms/uploads/attachment/file/855080/"
    "Salarios_Minimos_Generales_y_Profesionales_2009_2026_Zonas.xlsx"
)
CONASAMI_PAGE_URL = "https://www.gob.mx/conasami/documentos/consulta-de-salarios-minimos"
CONASAMI_START = "2013-01-01"
CONASAMI_END_YEAR = 2025

VIGENCIAS_PATH = INTERIM_DATA_DIR / "CONASAMI" / "vigencias_salario_minimo.csv"

# Zona que representa el salario "general" en cada periodo (inicio, zona).
# Hasta sep 2015 la zona B cubría la mayor parte del país.
_ZONA_GENERAL = [
    ("2013-01-01", "b"),
    ("2015-10-01", "unica"),
    ("2019-01-01", "restodelpais"),
    ("2025-01-01", "zsmg"),
]
_ZLFN_INICIO = "2019-01-01"


def download_conasami(output_path: Path) -> None:
    logger.info("\tDescargando salario mínimo de CONASAMI...")

    if output_path.exists():
        logger.info(f"Requerimiento CONASAMI previamente satisfecho: {output_path}")
        return

    response = requests.get(CONASAMI_URL, timeout=60)
    response.raise_for_status()
    if not response.content.startswith(b"PK"):
        raise ValueError("CONASAMI no devolvió un archivo xlsx válido.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    metadata = (
        "Fuente: Comisión Nacional de los Salarios Mínimos (CONASAMI)\n"
        f"Página: {CONASAMI_PAGE_URL}\n"
        f"URL de descarga: {CONASAMI_URL}\n"
        f"Fecha de descarga (UTC): {datetime.now(UTC).isoformat()}\n"
        "Unidad: Pesos mexicanos por día\n"
        "Frecuencia: Una fila por zona y cambio de vigencia (no es una serie mensual)\n"
        "Contenido: Salarios mínimos generales y profesionales 2009-2026 por zona, "
        "sin filtrar.\n"
        "Valores faltantes: Años sin cambio (p. ej. 2018) no tienen fila; el salario "
        "anterior sigue vigente.\n"
        f"Archivo de datos: {output_path.name}\n"
    )
    output_path.with_suffix(".txt").write_text(metadata, encoding="utf-8")

    logger.success(f"\tSalarios mínimos CONASAMI guardados en: {output_path}")


def _vigente_al_mes(vigencias: pd.DataFrame, meses: pd.DatetimeIndex, zona: str) -> pd.DataFrame:
    """Valor vigente al primer día de cada mes para una zona."""
    serie = vigencias.loc[vigencias["zona"] == zona].sort_values("inicio_vigencia")
    base = pd.DataFrame({"fecha": meses})
    return pd.merge_asof(
        base,
        serie[["inicio_vigencia", "salario_minimo_diario_mxn"]],
        left_on="fecha",
        right_on="inicio_vigencia",
    ).drop(columns="inicio_vigencia")


def process_conasami(raw_path: Path, output_path: Path) -> None:
    logger.info("Procesando salario mínimo de CONASAMI...")

    raw = pd.read_excel(raw_path, engine="openpyxl")
    vigencias = (
        raw[["inicio_vigencia", "zona", "salario_minimo_general"]]
        .rename(columns={"salario_minimo_general": "salario_minimo_diario_mxn"})
        .assign(
            inicio_vigencia=lambda d: pd.to_datetime(d["inicio_vigencia"]),
            salario_minimo_diario_mxn=lambda d: d["salario_minimo_diario_mxn"].round(2),
        )
        .sort_values(["inicio_vigencia", "zona"])
        .reset_index(drop=True)
    )
    VIGENCIAS_PATH.parent.mkdir(parents=True, exist_ok=True)
    vigencias.to_csv(VIGENCIAS_PATH, index=False)

    ultimo = vigencias["inicio_vigencia"].max()
    fin_serie = pd.Timestamp(year=max(ultimo.year, CONASAMI_END_YEAR), month=12, day=1)
    meses = pd.date_range(CONASAMI_START, fin_serie, freq="MS")

    partes = []
    for i, (inicio, zona) in enumerate(_ZONA_GENERAL):
        fin = (
            pd.Timestamp(_ZONA_GENERAL[i + 1][0])
            if i + 1 < len(_ZONA_GENERAL)
            else meses.max() + pd.offsets.MonthBegin(1)
        )
        tramo = meses[(meses >= inicio) & (meses < fin)]
        partes.append(
            _vigente_al_mes(vigencias, tramo, zona).assign(zona_original=zona, area="general")
        )
    zlfn_meses = meses[meses >= _ZLFN_INICIO]
    partes.append(
        _vigente_al_mes(vigencias, zlfn_meses, "zlfn").assign(zona_original="zlfn", area="zlfn")
    )

    tidy = (
        pd.concat(partes, ignore_index=True)
        .sort_values(["area", "fecha"])
        .reset_index(drop=True)[["fecha", "zona_original", "area", "salario_minimo_diario_mxn"]]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tidy.to_csv(output_path, index=False)

    logger.success(f"Salario mínimo mensual guardado en: {output_path}")
