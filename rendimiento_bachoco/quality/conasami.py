from pathlib import Path

from loguru import logger
import pandas as pd
from pandera.pandas import Check, Column, DataFrameSchema

# (fecha, area, valor esperado) verificados contra la fuente oficial.
_CONTROL = [
    ("2013-01-01", "general", 61.38),
    ("2016-01-01", "general", 73.04),
    ("2017-01-01", "general", 80.04),
    ("2017-12-01", "general", 88.36),
    ("2018-06-01", "general", 88.36),
    ("2019-01-01", "general", 102.68),
    ("2019-01-01", "zlfn", 176.72),
    ("2022-01-01", "general", 172.87),
    ("2022-01-01", "zlfn", 260.34),
    ("2024-01-01", "general", 248.93),
    ("2024-01-01", "zlfn", 374.89),
    ("2025-01-01", "general", 278.80),
    ("2025-01-01", "zlfn", 419.88),
]


def _meses_continuos(df: pd.DataFrame) -> bool:
    for _, g in df.groupby("area"):
        esperado = pd.date_range(g["fecha"].min(), g["fecha"].max(), freq="MS")
        if (
            len(g) != len(esperado)
            or not (g["fecha"].sort_values().values == esperado.values).all()
        ):
            return False
    return True


def _no_decreciente(df: pd.DataFrame) -> bool:
    return all(
        g.sort_values("fecha")["salario_minimo_diario_mxn"].is_monotonic_increasing
        for _, g in df.groupby("area")
    )


def _valores_control(df: pd.DataFrame) -> bool:
    idx = df.set_index([df["fecha"].dt.strftime("%Y-%m-%d"), "area"])["salario_minimo_diario_mxn"]
    return all((f, a) in idx.index and abs(idx[(f, a)] - v) < 0.005 for f, a, v in _CONTROL)


conasami_schema = DataFrameSchema(
    columns={
        "fecha": Column(
            "datetime64[ns]",
            Check(lambda s: s.dt.is_month_start, error="La fecha debe ser el primer día del mes"),
        ),
        "zona_original": Column(str),
        "area": Column(str, Check.isin(["general", "zlfn"])),
        "salario_minimo_diario_mxn": Column(float, Check.gt(0), nullable=False),
    },
    checks=[
        Check(
            lambda df: not df.duplicated(["fecha", "area"]).any(),
            error="Hay duplicados en (fecha, area)",
        ),
        Check(_meses_continuos, error="Los meses no son continuos en alguna área"),
        Check(
            _no_decreciente,
            error="El salario mínimo disminuye en el tiempo en alguna área",
        ),
        Check(
            _valores_control,
            error="Algún valor no coincide con los valores de control de CONASAMI",
        ),
    ],
    strict=True,
)


def validate_conasami(path: Path) -> None:
    df = pd.read_csv(path, parse_dates=["fecha"])
    df["fecha"] = df["fecha"].astype("datetime64[ns]")
    conasami_schema.validate(df)

    logger.success(f"\tEsquema de salario mínimo validado: {path}")
