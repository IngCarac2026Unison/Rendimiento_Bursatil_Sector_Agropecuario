from pathlib import Path

from loguru import logger
import pandas as pd
from pandera.pandas import Check, Column, DataFrameSchema


def _meses_continuos(df: pd.DataFrame) -> bool:
    for _, g in df.groupby("serie"):
        esperado = pd.date_range(g["fecha"].min(), g["fecha"].max(), freq="MS")
        if (
            len(g) != len(esperado)
            or not (g["fecha"].sort_values().values == esperado.values).all()
        ):
            return False
    return True


def _base_general(df: pd.DataFrame) -> bool:
    g = df[
        (df["serie"] == "general") & df["fecha"].isin(pd.to_datetime(["2018-07-01", "2018-08-01"]))
    ]
    return len(g) == 2 and abs(g["indice"].mean() - 100) < 1.5


inpc_schema = DataFrameSchema(
    columns={
        "fecha": Column(
            "datetime64[ns]",
            Check(lambda s: s.dt.is_month_start, error="La fecha debe ser el primer día del mes"),
        ),
        "serie": Column(str, Check.isin(["general", "tortilla_maiz", "maiz"])),
        "indice": Column(float, Check.gt(0), nullable=False),
        "var_mensual_pct": Column(float, nullable=True),
        "var_anual_pct": Column(float, nullable=True),
    },
    checks=[
        Check(
            lambda df: not df.duplicated(["fecha", "serie"]).any(),
            error="Hay duplicados en (fecha, serie)",
        ),
        Check(_meses_continuos, error="Los meses no son continuos en alguna serie"),
        Check(
            lambda df: (df["serie"] == "general").any(),
            error="Falta la serie general",
        ),
        Check(_base_general, error="El índice general no es ≈100 en 2018-07/08"),
    ],
    strict=True,
)


def validate_inpc(path: Path) -> None:
    df = pd.read_csv(path, parse_dates=["fecha"])
    df["fecha"] = df["fecha"].astype("datetime64[ns]")
    inpc_schema.validate(df)

    logger.success(f"\tEsquema de INPC validado: {path}")
