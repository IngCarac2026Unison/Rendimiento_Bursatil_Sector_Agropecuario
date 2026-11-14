from datetime import UTC, datetime
from pathlib import Path
import zipfile

from loguru import logger
import numpy as np
import pandas as pd
import requests

from rendimiento_bachoco.config import INTERIM_DATA_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR

ENIGH_YEARS = (2014, 2016, 2018, 2020, 2022, 2024)
ENIGH_RAW_DIR = RAW_DATA_DIR / "ENIGH"
ENIGH_INTERIM_DIR = INTERIM_DATA_DIR / "ENIGH"
ENIGH_PROCESSED_PATH = PROCESSED_DATA_DIR / "enigh_tortilla_hogar.csv"

ENIGH_PAGE_URL = "https://www.inegi.org.mx/programas/enigh/nc/"
_BASE_URL = "https://www.inegi.org.mx/contenidos/programas/enigh/nc"
_URL_2014 = f"{_BASE_URL}/2014/datosabiertos/enigh_ncv_2014_csv.zip"

# Clave de "tortilla de maíz" en el catálogo de gasto; en 2024 cambió el catálogo.
CLAVE_TORTILLA = {
    2014: "A004",
    2016: "A004",
    2018: "A004",
    2020: "A004",
    2022: "A004",
    2024: "011131",
}
DIAS_REFERENCIA = 7  # cantidad y gasto corresponden a la semana de levantamiento
_TIPOS_TOTAL = ("G1", "G3", "G5", "G6")


def _zip_path(raw_dir: Path, year: int, tabla: str | None) -> Path:
    if year == 2014:
        return raw_dir / "enigh_ncv_2014_csv.zip"
    return raw_dir / f"enigh{year}_ns_{tabla}_csv.zip"


def _urls(year: int) -> dict[Path, str]:
    if year == 2014:
        return {_zip_path(ENIGH_RAW_DIR, year, None): _URL_2014}
    return {
        _zip_path(
            ENIGH_RAW_DIR, year, t
        ): f"{_BASE_URL}/{year}/microdatos/enigh{year}_ns_{t}_csv.zip"
        for t in ("gastoshogar", "concentradohogar")
    }


def _fetch(url: str, path: Path) -> None:
    # HEAD devuelve text/html; se usa GET y se valida la firma del zip.
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        tmp = path.with_suffix(".part")
        with tmp.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    if not zipfile.is_zipfile(tmp):
        tmp.unlink()
        raise ValueError(f"ENIGH no devolvió un zip válido: {url}")
    tmp.replace(path)


def download_enigh(output_dir: Path = ENIGH_RAW_DIR, years: tuple[int, ...] = ENIGH_YEARS) -> None:
    logger.info("\tDescargando ENIGH (INEGI, Nueva Construcción)...")
    output_dir.mkdir(parents=True, exist_ok=True)

    for year in years:
        for path, url in _urls(year).items():
            target = output_dir / path.name
            if target.exists() and target.with_suffix(".txt").exists():
                logger.info(f"Requerimiento ENIGH previamente satisfecho: {target}")
                continue
            if not target.exists():
                _fetch(url, target)
            metadata = (
                "Fuente: INEGI, Encuesta Nacional de Ingresos y Gastos de los Hogares "
                f"(ENIGH) {year}, Nueva Construcción\n"
                f"Página: {ENIGH_PAGE_URL}\n"
                f"URL de descarga: {url}\n"
                f"Fecha de descarga (UTC): {datetime.now(UTC).isoformat()}\n"
                "Unidad: cantidad en kilogramos y gasto en pesos mexicanos corrientes, "
                "ambos de los 7 días de referencia\n"
                "Frecuencia: Encuesta bienal a hogares (levantamiento de agosto a noviembre)\n"
                "Contenido: Microdatos en CSV, sin filtrar"
                + (" (incluye todas las tablas del año).\n" if year == 2014 else ".\n")
                + f"Clave de tortilla de maíz: {CLAVE_TORTILLA[year]}\n"
                f"Archivo de datos: {target.name}\n"
            )
            target.with_suffix(".txt").write_text(metadata, encoding="utf-8")
            logger.success(f"\tENIGH guardado en: {target}")


def _read_member(zip_path: Path, nombre: str, **kwargs) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as zf:
        miembro = next(
            n
            for n in zf.namelist()
            if n.lower().endswith(f"/{nombre}.csv") or n == f"{nombre}.csv"
        )
        with zf.open(miembro) as f:
            return pd.read_csv(f, encoding="utf-8-sig", low_memory=False, **kwargs)


def _hogares_year(raw_dir: Path, year: int) -> pd.DataFrame:
    zg = _zip_path(raw_dir, year, "gastoshogar")
    zc = _zip_path(raw_dir, year, "concentradohogar")
    fac_col = "factor_hog" if year == 2014 else "factor"
    folios = {"folioviv": str, "foliohog": str}

    conc = _read_member(
        zc,
        "concentradohogar",
        usecols=["folioviv", "foliohog", fac_col, "tot_integ", "ing_cor"],
        dtype=folios,
    ).rename(columns={fac_col: "factor"})
    conc["folioviv"] = conc["folioviv"].str.zfill(10)
    conc["entidad"] = conc["folioviv"].str[:2]

    gastos = _read_member(
        zg,
        "gastoshogar",
        usecols=["folioviv", "foliohog", "clave", "tipo_gasto", "cantidad", "gasto"],
        dtype={**folios, "clave": str, "tipo_gasto": str},
    )
    gastos = gastos[gastos["clave"] == CLAVE_TORTILLA[year]].copy()
    gastos["folioviv"] = gastos["folioviv"].str.zfill(10)
    for col in ("cantidad", "gasto"):
        gastos[col] = pd.to_numeric(gastos[col], errors="coerce").fillna(0.0)

    llaves = ["folioviv", "foliohog"]
    g1 = (
        gastos[gastos["tipo_gasto"] == "G1"]
        .groupby(llaves)
        .agg(kg_sem_g1=("cantidad", "sum"), gasto_sem_g1=("gasto", "sum"))
    )
    total = (
        gastos[gastos["tipo_gasto"].isin(_TIPOS_TOTAL)]
        .groupby(llaves)
        .agg(kg_sem_total=("cantidad", "sum"))
    )
    hog = (
        conc.merge(g1, on=llaves, how="left")
        .merge(total, on=llaves, how="left")
        .fillna({"kg_sem_g1": 0.0, "gasto_sem_g1": 0.0, "kg_sem_total": 0.0})
    )
    for col in ("factor", "tot_integ", "ing_cor"):
        hog[col] = pd.to_numeric(hog[col], errors="coerce")
    return hog[
        [
            *llaves,
            "entidad",
            "factor",
            "tot_integ",
            "ing_cor",
            "kg_sem_g1",
            "gasto_sem_g1",
            "kg_sem_total",
        ]
    ]


def _decil_ponderado(ingreso: pd.Series, factor: pd.Series) -> pd.Series:
    orden = ingreso.sort_values(kind="mergesort").index
    acum = factor.loc[orden].cumsum() / factor.sum()
    decil = np.ceil(acum * 10 - 1e-9).clip(1, 10).astype(int)
    return decil.reindex(ingreso.index)


def _mediana_ponderada(valores: pd.Series, pesos: pd.Series) -> float:
    orden = valores.sort_values().index
    acum = pesos.loc[orden].cumsum()
    return float(valores.loc[orden][acum >= pesos.sum() / 2].iloc[0])


def _resumen(h: pd.DataFrame) -> dict:
    w = h["factor"]
    W = w.sum()
    compra = h["kg_sem_g1"] > 0
    wc = w[compra].sum()
    kg = (w * h["kg_sem_g1"]).sum()
    gasto = (w * h["gasto_sem_g1"]).sum()
    precios = (h["gasto_sem_g1"] / h["kg_sem_g1"])[compra & (h["gasto_sem_g1"] > 0)]
    d = DIAS_REFERENCIA
    return {
        "kg_dia_hogar": kg / W / d,
        "kg_dia_hogar_compradores": kg / wc / d if wc else np.nan,
        "kg_dia_hogar_total": (w * h["kg_sem_total"]).sum() / W / d,
        "gasto_dia_hogar_mxn": gasto / W / d,
        "precio_implicito_mxn_kg": gasto / kg if kg else np.nan,
        "precio_mediano_hogar_mxn_kg": (
            _mediana_ponderada(precios, w.loc[precios.index]) if len(precios) else np.nan
        ),
        "pct_hogares_compran": 100 * wc / W,
        "kg_dia_per_capita": kg / (w * h["tot_integ"]).sum() / d,
        "n_hogares_muestra": len(h),
        "hogares_expandidos": W,
    }


def process_enigh(raw_dir: Path = ENIGH_RAW_DIR, output_path: Path = ENIGH_PROCESSED_PATH) -> None:
    logger.info("Procesando ENIGH: tortilla de maíz por hogar...")
    ENIGH_INTERIM_DIR.mkdir(parents=True, exist_ok=True)

    filas = []
    for year in ENIGH_YEARS:
        hog = _hogares_year(raw_dir, year)
        hog.to_parquet(ENIGH_INTERIM_DIR / f"tortilla_hogar_{year}.parquet", index=False)

        hog = hog.dropna(subset=["factor"]).reset_index(drop=True)
        hog["decil"] = _decil_ponderado(hog["ing_cor"].fillna(0.0), hog["factor"])

        filas.append(
            {"anio": year, "nivel": "nacional", "clave_nivel": "nacional", **_resumen(hog)}
        )
        for ent, g in hog.groupby("entidad"):
            filas.append({"anio": year, "nivel": "entidad", "clave_nivel": ent, **_resumen(g)})
        for dec, g in hog.groupby("decil"):
            filas.append({"anio": year, "nivel": "decil", "clave_nivel": str(dec), **_resumen(g)})

    tidy = pd.DataFrame(filas)
    tidy["hogares_expandidos"] = tidy["hogares_expandidos"].round().astype(int)
    tidy = tidy.round(
        {c: 4 for c in tidy.columns if c.startswith(("kg_", "gasto_", "precio_"))}
        | {"pct_hogares_compran": 2}
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tidy.to_csv(output_path, index=False)

    logger.success(f"ENIGH tortilla por hogar guardado en: {output_path}")
