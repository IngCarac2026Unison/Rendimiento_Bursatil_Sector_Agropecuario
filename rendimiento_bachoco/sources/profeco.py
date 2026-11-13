import csv
from datetime import UTC, datetime
import hashlib
import io
from pathlib import Path
import subprocess
import unicodedata

from loguru import logger
import pandas as pd
import requests

from rendimiento_bachoco.config import INTERIM_DATA_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR

PROFECO_PAGE_URL = "https://datos.profeco.gob.mx/index.php"
PROFECO_URL = "https://datos.profeco.gob.mx/docs/qqp/QQP_{year}.rar"
PROFECO_META_URL = "https://datos.profeco.gob.mx/docs/qqp/QQP_metadatos_dataset.csv"
PROFECO_YEARS = list(range(2015, 2027))

PROFECO_RAW_DIR = RAW_DATA_DIR / "PROFECO"
INTERIM_PATH = INTERIM_DATA_DIR / "PROFECO" / "qqp_tortilla_maiz.parquet"
PROCESSED_PATH = PROCESSED_DATA_DIR / "precio_tortilla_mensual.csv"

_CHUNK = 1 << 20
_PRESENTACION_KG = "1 Kg. Granel"
_GIROS_SALIDA = ["tortilleria", "autoservicio"]

ESTADOS = [
    "Aguascalientes",
    "Baja California",
    "Baja California Sur",
    "Campeche",
    "Chiapas",
    "Chihuahua",
    "Ciudad de México",
    "Coahuila",
    "Colima",
    "Durango",
    "Estado de México",
    "Guanajuato",
    "Guerrero",
    "Hidalgo",
    "Jalisco",
    "Michoacán",
    "Morelos",
    "Nayarit",
    "Nuevo León",
    "Oaxaca",
    "Puebla",
    "Querétaro",
    "Quintana Roo",
    "San Luis Potosí",
    "Sinaloa",
    "Sonora",
    "Tabasco",
    "Tamaulipas",
    "Tlaxcala",
    "Veracruz",
    "Yucatán",
    "Zacatecas",
]

# Nombres alternativos de columnas entre años -> nombre normalizado.
_ALIAS = {
    "producto": "producto",
    "presentacion": "presentacion",
    "presentación": "presentacion",
    "precio": "precio",
    "fecha_registro": "fecha",
    "fecharegistro": "fecha",
    "fecha": "fecha",
    "cadena_comercial": "cadena_comercial",
    "cadenacomercial": "cadena_comercial",
    "giro": "giro",
    "nombre_comercial": "nombre_comercial",
    "nombrecomercial": "nombre_comercial",
    "direccion": "direccion",
    "dirección": "direccion",
    "estado": "estado",
    "entidad": "estado",
    "municipio": "municipio",
}
_COLS_SALIDA = [
    "fecha",
    "estado",
    "municipio",
    "giro",
    "cadena_comercial",
    "nombre_comercial",
    "direccion",
    "presentacion",
    "precio_mxn",
]


def _sin_acentos(texto: object) -> str:
    if pd.isna(texto):
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in nfkd if not unicodedata.combining(c)).strip().lower()


_ESTADO_CANONICO = {_sin_acentos(e): e for e in ESTADOS}


def _normalizar_giro(giro: object) -> str:
    g = _sin_acentos(giro)
    if "tortiller" in g:
        return "tortilleria"
    if "autoservicio" in g or "supermercado" in g:
        return "autoservicio"
    return g


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(_CHUNK):
            h.update(chunk)
    return h.hexdigest()


def _descargar(url: str, destino: Path) -> None:
    tmp = destino.with_suffix(destino.suffix + ".part")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in r.iter_content(_CHUNK):
                f.write(chunk)
    tmp.replace(destino)


def download_profeco(output_dir: Path = PROFECO_RAW_DIR, years: list[int] | None = None) -> None:
    logger.info("\tDescargando precios QQP de PROFECO...")
    output_dir.mkdir(parents=True, exist_ok=True)
    years = years or PROFECO_YEARS

    meta_path = output_dir / "QQP_metadatos_dataset.csv"
    if not meta_path.exists():
        _descargar(PROFECO_META_URL, meta_path)

    for year in years:
        path = output_dir / f"QQP_{year}.rar"
        url = PROFECO_URL.format(year=year)
        if not path.exists():
            try:
                _descargar(url, path)
            except requests.RequestException as e:
                logger.warning(f"\tNo se pudo descargar PROFECO {year}: {e}")
                continue
            logger.success(f"\tPROFECO {year} guardado en: {path}")
        else:
            logger.info(f"Requerimiento PROFECO {year} previamente satisfecho: {path}")
        if not path.with_suffix(".txt").exists():
            _escribir_metadata(path, year, url)

    _registrar_duplicados(output_dir)


def _escribir_metadata(path: Path, year: int, url: str) -> None:
    metadata = (
        "Fuente: Procuraduría Federal del Consumidor (PROFECO), Quién es Quién en los Precios\n"
        f"Página: {PROFECO_PAGE_URL}\n"
        f"URL de descarga: {url}\n"
        f"Metadatos del conjunto: {PROFECO_META_URL}\n"
        f"Fecha de descarga (UTC): {datetime.now(UTC).isoformat()}\n"
        "Unidad: Pesos mexicanos por presentación del producto (p. ej. 1 kg a granel)\n"
        "Frecuencia: Un CSV por quincena con un registro por producto y establecimiento\n"
        f"Contenido: Todos los productos del programa en {year}, sin filtrar.\n"
        "Valores faltantes: El archivo publicado es solo el primer volumen de un RAR "
        "multivolumen: contiene las primeras quincenas del año y la última está truncada.\n"
        f"SHA-256: {_sha256(path)}\n"
        f"Archivo de datos: {path.name}\n"
    )
    path.with_suffix(".txt").write_text(metadata, encoding="utf-8")


def _registrar_duplicados(output_dir: Path) -> None:
    """Anota en los .txt los años cuyo archivo es idéntico a otro."""
    hashes: dict[str, list[Path]] = {}
    for path in sorted(output_dir.glob("QQP_[0-9]*.rar")):
        hashes.setdefault(_sha256(path), []).append(path)
    for paths in hashes.values():
        for path in paths:
            txt = path.with_suffix(".txt")
            if not txt.exists():
                continue
            lineas = [
                ln
                for ln in txt.read_text(encoding="utf-8").splitlines()
                if not ln.startswith("Archivo idéntico a:")
            ]
            otros = [p.name for p in paths if p != path]
            if otros:
                logger.warning(f"\t{path.name} es idéntico a {', '.join(otros)}")
                lineas.append(f"Archivo idéntico a: {', '.join(otros)}")
            txt.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def _listar_csv(rar: Path) -> list[tuple[str, int]]:
    """Nombre y tamaño de cada CSV del RAR (bsdtar lista aunque el RAR esté incompleto)."""
    out = subprocess.run(
        ["bsdtar", "-tvf", str(rar)], capture_output=True, text=True, check=False
    ).stdout
    items = []
    for ln in out.splitlines():
        partes = ln.split(maxsplit=8)
        if len(partes) == 9 and partes[8].lower().endswith(".csv"):
            items.append((partes[8], int(partes[4])))
    return sorted(items)


def _filtrar_csv(texto: str) -> pd.DataFrame:
    """Devuelve los registros de tortilla de maíz de un CSV quincenal."""
    reader = csv.reader(io.StringIO(texto, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        return pd.DataFrame()
    cols = [_ALIAS.get(c.strip().lower().lstrip("﻿"), c) for c in header]
    if "producto" not in cols or "precio" not in cols:
        return pd.DataFrame()
    ip = cols.index("producto")
    filas = [
        r
        for r in reader
        if len(r) == len(cols)
        and "tortilla" in r[ip].lower()
        and "ma" in r[ip].lower()
        and "harina" not in r[ip].lower()
    ]
    df = pd.DataFrame(filas, columns=cols)
    return df.loc[:, ~df.columns.duplicated()]


def _normalizar(df: pd.DataFrame) -> pd.DataFrame:
    for c in _COLS_SALIDA[:-1]:
        if c not in df:
            df[c] = pd.NA
    df["fecha"] = pd.to_datetime(df["fecha"].str.strip(), format="mixed", errors="coerce")
    df["precio_mxn"] = pd.to_numeric(df["precio"], errors="coerce")
    for c in ("estado", "municipio", "giro", "cadena_comercial", "presentacion"):
        df[c] = df[c].astype("string").str.strip()
    df["estado"] = df["estado"].map(lambda e: _ESTADO_CANONICO.get(_sin_acentos(e), e))
    df["giro"] = df["giro"].map(_normalizar_giro)
    return df[_COLS_SALIDA]


def process_profeco(
    raw_dir: Path = PROFECO_RAW_DIR,
    output_dir: Path = PROCESSED_PATH.parent,
    interim_path: Path = INTERIM_PATH,
) -> None:
    logger.info("Procesando precios de tortilla de PROFECO...")
    partes = []
    for rar in sorted(raw_dir.glob("QQP_[0-9]*.rar")):
        year = rar.stem.split("_")[1]
        n_antes = len(partes)
        for nombre, tamano in _listar_csv(rar):
            r = subprocess.run(
                ["bsdtar", "-xOf", str(rar), nombre], capture_output=True, check=False
            )
            if len(r.stdout) != tamano:
                # El archivo publicado contiene solo el primer volumen del RAR.
                logger.warning(f"\t{nombre}: archivo truncado en la fuente, se omite")
                continue
            texto = r.stdout.decode("utf-8-sig", errors="replace")
            df = _filtrar_csv(texto)
            if not df.empty:
                partes.append(_normalizar(df))
        n = sum(len(p) for p in partes[n_antes:])
        if n:
            logger.info(f"\t{year}: {n} registros de tortilla de maíz")
        else:
            logger.warning(f"\t{year}: sin registros utilizables de tortilla de maíz")

    if not partes:
        raise ValueError("No se encontraron registros de tortilla de maíz en PROFECO.")
    reg = (
        pd.concat(partes, ignore_index=True)
        .dropna(subset=["fecha", "precio_mxn", "estado"])
        .sort_values(["fecha", "estado", "municipio"])
        .reset_index(drop=True)
    )
    interim_path.parent.mkdir(parents=True, exist_ok=True)
    reg.to_parquet(interim_path, index=False)

    tidy = _agregar_mensual(reg)
    output_dir.mkdir(parents=True, exist_ok=True)
    tidy.to_csv(output_dir / PROCESSED_PATH.name, index=False)
    logger.success(f"Precio mensual de tortilla guardado en: {output_dir / PROCESSED_PATH.name}")


def _estadisticos(g: pd.core.groupby.DataFrameGroupBy) -> pd.DataFrame:
    return g.agg(
        precio_mediana_mxn_kg=("precio_mxn", "median"),
        precio_p25=("precio_mxn", lambda s: s.quantile(0.25)),
        precio_p75=("precio_mxn", lambda s: s.quantile(0.75)),
        n_registros=("precio_mxn", "size"),
        n_establecimientos=("establecimiento", "nunique"),
    ).reset_index()


def _agregar_mensual(reg: pd.DataFrame) -> pd.DataFrame:
    kg = reg.loc[
        (reg["presentacion"] == _PRESENTACION_KG) & reg["giro"].isin(_GIROS_SALIDA)
    ].copy()
    kg["mes"] = kg["fecha"].dt.to_period("M").dt.to_timestamp()
    kg["establecimiento"] = (
        kg["cadena_comercial"].fillna("")
        + "|"
        + kg["nombre_comercial"].fillna("")
        + "|"
        + kg["direccion"].fillna("")
    )

    estatal = _estadisticos(kg.groupby(["mes", "giro", "estado"]))
    estatal["nivel"] = "estado"

    # Nacional: mediana de las medianas estatales (cada estado pesa igual).
    nac = kg.groupby(["mes", "giro"])
    nacional = nac.agg(
        n_registros=("precio_mxn", "size"), n_establecimientos=("establecimiento", "nunique")
    )
    med = estatal.groupby(["mes", "giro"])["precio_mediana_mxn_kg"]
    nacional["precio_mediana_mxn_kg"] = med.median()
    nacional["precio_p25"] = med.quantile(0.25)
    nacional["precio_p75"] = med.quantile(0.75)
    nacional = nacional.reset_index().assign(nivel="nacional", estado=pd.NA)

    out = pd.concat([nacional, estatal], ignore_index=True).rename(columns={"mes": "fecha"})
    out = out.sort_values(["nivel", "giro", "estado", "fecha"], na_position="first")
    cols = [
        "fecha",
        "nivel",
        "estado",
        "giro",
        "precio_mediana_mxn_kg",
        "precio_p25",
        "precio_p75",
        "n_registros",
        "n_establecimientos",
    ]
    out[cols[4:7]] = out[cols[4:7]].round(2)
    return out[cols].reset_index(drop=True)
