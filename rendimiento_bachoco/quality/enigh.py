from pathlib import Path

from loguru import logger
import pandas as pd
from pandera.pandas import Check, Column, DataFrameSchema

ANIOS = (2014, 2016, 2018, 2020, 2022, 2024)

# kg/día por hogar nacional (compra monetaria, todos los hogares).
_CONTROL_KG_DIA = {2014: 0.543, 2016: 0.514, 2018: 0.514, 2020: 0.525, 2022: 0.485, 2024: 0.455}
_TOLERANCIA = 0.02


def _anios_completos(df: pd.DataFrame) -> bool:
    return set(df["anio"]) == set(ANIOS) and all(
        (df.loc[df["anio"] == a, "nivel"] == "nacional").sum() == 1 for a in ANIOS
    )


def _control_nacional(df: pd.DataFrame) -> bool:
    nac = df[df["nivel"] == "nacional"].set_index("anio")["kg_dia_hogar"]
    return all(
        a in nac.index and abs(nac[a] / v - 1) <= _TOLERANCIA for a, v in _CONTROL_KG_DIA.items()
    )


def _entidades(df: pd.DataFrame) -> bool:
    ent = df[df["nivel"] == "entidad"].groupby("anio")["clave_nivel"].nunique()
    return all(ent.get(a, 0) == 32 for a in ANIOS)


def _deciles(df: pd.DataFrame) -> bool:
    dec = df[df["nivel"] == "decil"].groupby("anio")["clave_nivel"].nunique()
    return all(dec.get(a, 0) == 10 for a in ANIOS)


_no_negativo = Check.ge(0)

enigh_schema = DataFrameSchema(
    columns={
        "anio": Column(int, Check.isin(ANIOS)),
        "nivel": Column(str, Check.isin(["nacional", "entidad", "decil"])),
        "clave_nivel": Column(str),
        "kg_dia_hogar": Column(float, _no_negativo),
        "kg_dia_hogar_compradores": Column(float, _no_negativo),
        "kg_dia_hogar_total": Column(float, _no_negativo),
        "gasto_dia_hogar_mxn": Column(float, _no_negativo),
        "precio_implicito_mxn_kg": Column(float, Check.in_range(5, 60)),
        "precio_mediano_hogar_mxn_kg": Column(float, Check.gt(0)),
        "pct_hogares_compran": Column(float, Check.in_range(0, 100)),
        "kg_dia_per_capita": Column(float, _no_negativo),
        "n_hogares_muestra": Column(int, Check.gt(0)),
        "hogares_expandidos": Column(int, Check.gt(0)),
    },
    checks=[
        Check(_anios_completos, error="Faltan años esperados o el nivel nacional no es único"),
        Check(
            lambda df: not df.duplicated(["anio", "nivel", "clave_nivel"]).any(),
            error="Hay duplicados en (anio, nivel, clave_nivel)",
        ),
        Check(_entidades, error="Cada año debe tener exactamente 32 entidades"),
        Check(_deciles, error="Cada año debe tener exactamente 10 deciles"),
        Check(
            _control_nacional,
            error="kg_dia_hogar nacional se desvía más de 2% de los valores de control",
        ),
    ],
    strict=True,
)


def validate_enigh(path: Path) -> None:
    df = pd.read_csv(path, dtype={"clave_nivel": str})
    enigh_schema.validate(df)

    logger.success(f"\tEsquema de ENIGH validado: {path}")
